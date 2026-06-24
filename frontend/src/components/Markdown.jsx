// A tiny, dependency-free markdown renderer — just enough for the short markdown
// the AI review returns: paragraphs, **bold**, `inline code`, `-`/`*` bullet
// lists, fenced ```code``` blocks, and # headings. Not a full CommonMark parser;
// it deliberately handles only what Gemini emits, keeping the bundle small.

// Render a single line of inline text, turning **bold** and `code` into nodes.
function renderInline(text) {
  const nodes = [];
  const regex = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let lastIndex = 0;
  let key = 0;
  let match;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) nodes.push(text.slice(lastIndex, match.index));
    const token = match[0];
    if (token.startsWith('**')) {
      nodes.push(
        <strong key={key++} className="font-semibold text-slate-100">{token.slice(2, -2)}</strong>,
      );
    } else {
      nodes.push(
        <code key={key++} className="rounded bg-slate-800 px-1 py-0.5 font-mono text-[12px] text-violet-200">
          {token.slice(1, -1)}
        </code>,
      );
    }
    lastIndex = match.index + token.length;
  }
  if (lastIndex < text.length) nodes.push(text.slice(lastIndex));
  return nodes;
}

function Markdown({ text }) {
  const lines = (text || '').replace(/\r\n/g, '\n').split('\n');
  const blocks = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code block ``` ... ```
    if (line.trim().startsWith('```')) {
      const code = [];
      i += 1;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        code.push(lines[i]);
        i += 1;
      }
      i += 1; // skip the closing fence
      blocks.push(
        <pre key={key++} className="my-2 overflow-auto rounded bg-[#050812] p-3 font-mono text-xs text-slate-200">
          {code.join('\n')}
        </pre>,
      );
      continue;
    }

    // Bullet list (- item / * item)
    if (/^\s*[-*]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ''));
        i += 1;
      }
      blocks.push(
        <ul key={key++} className="my-2 list-disc space-y-1 pl-5">
          {items.map((item, idx) => (
            <li key={idx}>{renderInline(item)}</li>
          ))}
        </ul>,
      );
      continue;
    }

    // Heading (#, ##, ###)
    const heading = /^(#{1,4})\s+(.*)$/.exec(line);
    if (heading) {
      blocks.push(
        <p key={key++} className="mb-1 mt-3 font-semibold text-slate-100">{renderInline(heading[2])}</p>,
      );
      i += 1;
      continue;
    }

    // Blank line — skip.
    if (line.trim() === '') {
      i += 1;
      continue;
    }

    // Paragraph — gather consecutive "plain" lines.
    const para = [];
    while (
      i < lines.length
      && lines[i].trim() !== ''
      && !lines[i].trim().startsWith('```')
      && !/^\s*[-*]\s+/.test(lines[i])
      && !/^#{1,4}\s+/.test(lines[i])
    ) {
      para.push(lines[i]);
      i += 1;
    }
    blocks.push(
      <p key={key++} className="my-2 leading-6">{renderInline(para.join(' '))}</p>,
    );
  }

  return <div className="text-sm text-slate-300">{blocks}</div>;
}

export default Markdown;
