// Verify replacement reference solutions for invertTree and isSubtree.
function invertTree(arr) {
  if (!arr.length) return [];
  const r = [];
  let start = 0, width = 1;
  while (start < arr.length) {
    const level = arr.slice(start, start + width);
    while (level.length < width) level.push(null);
    r.push(...level.reverse());
    start += width;
    width *= 2;
  }
  return r.slice(0, arr.length);
}

function isSubtree(s, t) {
  const sub = (i) => {
    const out = [];
    const walk = (j, depth) => {
      if (j >= s.length || s[j] === null || s[j] === undefined) return;
      out.push([depth, s[j]]);
      walk(2 * j + 1, depth + 1);
      walk(2 * j + 2, depth + 1);
    };
    walk(i, 0);
    return out;
  };
  const flat = (a) => {
    const out = [];
    const walk = (j, depth) => {
      if (j >= a.length || a[j] === null || a[j] === undefined) return;
      out.push([depth, a[j]]);
      walk(2 * j + 1, depth + 1);
      walk(2 * j + 2, depth + 1);
    };
    walk(0, 0);
    return out;
  };
  const target = JSON.stringify(flat(t));
  for (let i = 0; i < s.length; i++) {
    if (s[i] === null || s[i] === undefined) continue;
    if (JSON.stringify(sub(i)) === target) return true;
  }
  return false;
}

const chk = (label, got, want) => {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  console.log(ok ? "PASS" : "FAIL", label, "got", JSON.stringify(got), "want", JSON.stringify(want));
};

chk("invert1", invertTree([4, 2, 7, 1, 3, 6, 9]), [4, 7, 2, 9, 6, 3, 1]);
chk("invert2", invertTree([2, 1, 3]), [2, 3, 1]);
chk("invert3", invertTree([]), []);
chk("sub1", isSubtree([3, 4, 5, 1, 2], [4, 1, 2]), true);
chk("sub2", isSubtree([3, 4, 5, 1, 2, null, null, null, null, 0], [4, 1, 2]), false);
