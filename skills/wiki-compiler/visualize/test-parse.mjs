#!/usr/bin/env node
/**
 * Index-parsing regression tests. Run: node test-parse.mjs
 *
 * Caught 2026-08-20: the parser read only markdown links, while SKILL.md and
 * the template both emit wiki-links — on a real INDEX.md the graph came out
 * empty. Two more shifts hid behind it: dropping empty cells moved every later
 * column, and fixed positions mismatched the 4-column template.
 */
import assert from 'node:assert/strict';
import path from 'node:path';
import { readFileSync, writeFileSync, unlinkSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const src = readFileSync(path.join(here, 'server.js'), 'utf8');
const slice = src.slice(
  src.indexOf('// Split a markdown table row'),
  src.indexOf('function parseSections')
);
const tmp = path.join(here, '.parse-under-test.mjs');
writeFileSync(tmp, `import path from 'node:path';\n${slice}\nexport { parseIndexTopics };\n`);
const { parseIndexTopics } = await import(`file://${tmp}`);
unlinkSync(tmp);

const rows = (...lines) => `## Topics\n\n${lines.join('\n')}\n`;

// 1. Documented 5-column layout with wiki-links, one topic without aliases.
const five = parseIndexTopics(rows(
  '| Topic | Also Known As | Sources | Last Updated | Status |',
  '|-------|---------------|--------:|--------------|--------|',
  '| [[topics/ai-agent]] | agent, factory | 119 | 2026-08-10 | active |',
  '| [[topics/calendar]] |  | 11 | 2026-08-09 | active |'
));
assert.equal(five.length, 2, 'wiki-links must be recognised');
assert.equal(five[0].sourceCount, 119);
assert.deepEqual(
  [five[1].slug, five[1].aliases, five[1].sourceCount, five[1].lastUpdated],
  ['calendar', '', 11, '2026-08-09'],
  'an empty aliases cell must not shift the later columns'
);

// 2. The template ships 4 columns — no "Also Known As".
const four = parseIndexTopics(rows(
  '| Topic | Sources | Last Updated | Status |',
  '|-------|---------|-------------|--------|',
  '| [[topics/mail]] | 42 | 2026-08-01 | active |'
));
assert.equal(four[0].sourceCount, 42, 'count must come from the Sources column, not by position');
assert.equal(four[0].lastUpdated, '2026-08-01');

// 3. Markdown links stay supported, display name wins over the slug.
const md = parseIndexTopics(rows(
  '| Topic | Sources | Last Updated | Status |',
  '|-------|---------|-------------|--------|',
  '| [Mail](topics/mail.md) | 7 | 2026-08-02 | active |'
));
assert.deepEqual([md[0].slug, md[0].name], ['mail', 'Mail']);

// 4. Prose quoting the header is not a table.
assert.deepEqual(
  parseIndexTopics('Header looks like "| Topic |" here.\n| [[topics/ghost]] | 5 | x | active |\n'),
  [],
  'a header match must start the row'
);

console.log('index parsing: 4/4 ok');
