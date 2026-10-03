// The gene finder, running in the page. No server, no network.
//
// Written as a plain script rather than a module, and fed by scripts rather
// than by fetch, so the page works the same opened off a web address or
// double-clicked out of a folder. A page opened off the disk is not allowed
// to fetch the files next to it, but it is always allowed to load a script.
//
// The model is 4 lookup tables of numbers. A run of 5 to 8 DNA letters packs
// into a number, 2 bits a letter, so finding a run's weight is reading an
// array by position: no searching and no hashing.
//
// This is the same arithmetic scikit-learn does, checked against it before
// the tables were exported. Count the runs, take 1 + ln(count), multiply by
// the run's idf, make the vector length 1, dot it with the weights, add the
// intercept, squash.
window.Finder = (function () {
  var META = null, IDF = [], COEF = [], K = [];

  function bytes(b64) {
    var s = atob(b64), out = new Uint8Array(s.length);
    for (var i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
    return out;
  }

  // Both of these are set by the scripts the page loads.
  function load() {
    META = window.NITROBE_META;
    K = META.ks;
    var raw = new Int16Array(bytes(window.NITROBE_BIN).buffer);
    var at = 0;
    IDF = []; COEF = [];
    for (var i = 0; i < K.length; i++) {
      var n = Math.pow(4, K[i]);
      IDF.push(raw.subarray(at, at + n)); at += n;
      COEF.push(raw.subarray(at, at + n)); at += n;
    }
    return META;
  }

  // A genome arrives packed 2 bits a letter. Unpacked to 1 byte a letter it
  // is easier to walk and still only a few megabytes.
  function genome(g, packed) {
    var buf = bytes(packed), seq = new Uint8Array(g.letters);
    for (var i = 0; i < g.letters; i++) seq[i] = (buf[i >> 2] >> (6 - 2 * (i & 3))) & 3;
    // The gaps, so no run touching one is counted. An assembly has stretches
    // where the letters were never resolved, and the model has never seen a
    // run with a gap in it.
    var gap = new Uint8Array(g.letters), gs = g.gaps || [];
    for (var j = 0; j < gs.length; j++) gap.fill(1, gs[j][0], gs[j][0] + gs[j][1]);
    return { seq: seq, gap: gap, letters: g.letters };
  }

  var LETTER = ["A", "C", "G", "T"];
  function text(seq, a, b) {
    var s = "";
    for (var i = a; i < b; i++) s += LETTER[seq[i]];
    return s;
  }

  // Scratch space, reused for every window so the loop allocates nothing.
  var acc = null, touched = null;
  function ready() {
    if (acc) return;
    acc = []; touched = [];
    for (var i = 0; i < K.length; i++) {
      acc.push(new Float32Array(Math.pow(4, K[i])));
      touched.push(new Int32Array(Math.pow(4, K[i])));
    }
  }

  // Score one window. dir of -1 reads it off the other strand, which means
  // reversing the order and complementing every letter.
  function score(seq, gap, from, len, dir) {
    ready();
    var SCALE = META.scale, dot = 0, sq = 0;
    for (var ki = 0; ki < K.length; ki++) {
      var k = K[ki], mask = Math.pow(4, k) - 1;
      var a = acc[ki], seen = touched[ki], idf = IDF[ki], coef = COEF[ki];
      var used = 0, code = 0, good = 0;
      for (var j = 0; j < len; j++) {
        var i = dir > 0 ? from + j : from + len - 1 - j;
        if (gap[i]) { good = 0; code = 0; continue; }
        var base = dir > 0 ? seq[i] : 3 - seq[i];
        code = ((code * 4) + base) % (mask + 1);
        if (++good < k) continue;
        if (a[code] === 0) seen[used++] = code;
        a[code] += 1;
      }
      for (var t = 0; t < used; t++) {
        var c = seen[t], d = idf[c];
        if (d !== 0) {
          var v = (1 + Math.log(a[c])) * (d / SCALE);
          sq += v * v;
          dot += v * (coef[c] / SCALE);
        }
        a[c] = 0;
      }
    }
    if (sq === 0) return 0;
    return 1 / (1 + Math.exp(-(dot / Math.sqrt(sq) + META.intercept)));
  }

  // Walk the whole genome, both ways round, reporting progress as it goes.
  function sweep(g, onProgress) {
    var W = META.window, S = META.step, starts = [];
    for (var s = 0; s + W <= g.letters; s += S) starts.push(s);
    var pts = new Array(starts.length), best = null;
    var chunk = Math.max(1, Math.ceil(starts.length / 60)), i = 0;
    return new Promise(function (done) {
      function piece() {
        var end = Math.min(starts.length, i + chunk);
        for (var j = i; j < end; j++) {
          var at = starts[j];
          var f = score(g.seq, g.gap, at, W, 1);
          var r = score(g.seq, g.gap, at, W, -1);
          var v = f >= r ? f : r;
          pts[j] = [at, v, f >= r ? "+" : "-"];
          if (!best || v > best[1]) best = pts[j];
        }
        i = end;
        onProgress(pts.slice(0, end), end / starts.length, best, starts.length);
        if (i < starts.length) setTimeout(piece, 0);     // let the page repaint
        else done({ points: pts, best: best, windows: starts.length });
      }
      piece();
    });
  }

  // Once the gene is found, read that spot again in small pieces so every
  // letter can be shaded by how much it looks like the gene.
  function closeup(g, at, dir) {
    var W = META.window, F = META.fine, FS = META.fine_step, pad = 900;
    var a = Math.max(0, at - pad), b = Math.min(g.letters, at + W + pad), n = b - a;
    var hot = new Float32Array(n), seen = new Float32Array(n);
    for (var s = 0; s + F <= n; s += FS) {
      var v = score(g.seq, g.gap, a + s, F, dir === "-" ? -1 : 1);
      for (var i = s; i < s + F; i++) { hot[i] += v; seen[i] += 1; }
    }
    for (var i2 = 0; i2 < n; i2++) hot[i2] /= Math.max(1, seen[i2]);
    return { start: a, dna: text(g.seq, a, b), heat: hot,
             window: [at, at + W], pieces: Math.floor((n - F) / FS) + 1 };
  }

  return { load: load, genome: genome, sweep: sweep, closeup: closeup,
           score: score, text: text, meta: function () { return META; } };
})();
