// news-image-20261126 entrypoint: hand the pre-rendered front page to the
// grader by copying it into the output directory. The page itself is drawn
// at build time by scripts/compose.py from the five verified stories of
// Thursday 26 November 2026; this file never draws or edits the image, it
// only proves the copy is a genuine 1024x1024 PNG under the 1 MiB cap and
// byte-identical to the repository file. Node 22, standard library only.
import { copyFileSync, mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

// PNG file signature, the 12-byte IEND trailer, and the entry limits.
const PNG_SIGNATURE = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
const PNG_END_MARKER = "\0\0\0\0IEND\xaeB`\x82";
const MAX_BYTES = 1048576;
const EXPECTED_SIDE = 1024;

function checkPng(bytes: Buffer): void {
  for (let i = 0; i < PNG_SIGNATURE.length; i++) {
    if (bytes[i] !== PNG_SIGNATURE[i]) {
      throw new Error("entry.png is not a PNG file");
    }
  }
  if (bytes.length > MAX_BYTES) {
    throw new Error(`entry.png is ${bytes.length} bytes, over the 1 MiB cap`);
  }
  // IHDR stores width at bytes 16-19 and height at 20-23, big-endian.
  const width = bytes.readUInt32BE(16);
  const height = bytes.readUInt32BE(20);
  if (width !== EXPECTED_SIDE || height !== EXPECTED_SIDE) {
    throw new Error(`entry.png is ${width}x${height}, expected 1024x1024`);
  }
  const tail = bytes.subarray(bytes.length - 12).toString("latin1");
  if (tail !== PNG_END_MARKER) {
    throw new Error("entry.png is missing a valid trailing IEND chunk");
  }
}

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const source = new URL("./entry.png", import.meta.url);
const original = readFileSync(source);
checkPng(original);

mkdirSync(outDir, { recursive: true });
const dest = join(outDir, "entry.png");
copyFileSync(source, dest);

// Prove the copy: re-read it and byte-compare against the repository file.
const copied = readFileSync(dest);
if (!copied.equals(original)) {
  throw new Error("copied entry.png differs from the source");
}
console.log(
  `wrote ${dest} (${copied.length} bytes, 1024x1024 PNG, verified identical)`,
);
