import Markdown from 'react-markdown';
import { memo } from 'react';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

export type LectureSource = { label: string; chunk_id: string; page: number | null; section_path: string[] };

type MdNode = { type: string; value?: string; url?: string; children?: MdNode[] };

function LectureMarkdown({ text, sources = [], onSource, allowLinks = true, gfm = false }: {
  text: string; sources?: LectureSource[]; onSource?: (page: number) => void; allowLinks?: boolean; gfm?: boolean;
}) {
  const registered = new Map(sources.filter(source => /^S[1-9]\d*$/.test(source.label)
    && Number.isInteger(source.page) && source.page! > 0).map(source => [source.label, source]));
  const citations = () => (tree: MdNode) => {
    const visit = (node: MdNode) => {
      if (!node.children || ['link', 'code', 'inlineCode', 'math', 'inlineMath', 'html'].includes(node.type)) return;
      node.children = node.children.flatMap(child => {
        if (child.type !== 'text') { visit(child); return [child]; }
        const value = child.value ?? '';
        const result: MdNode[] = [];
        let start = 0;
        for (const match of value.matchAll(/\[(S[1-9]\d*)\]/g)) {
          if (!registered.has(match[1])) continue;
          result.push({ type: 'text', value: value.slice(start, match.index) },
            { type: 'link', url: `#wf-source-${match[1]}`, children: [{ type: 'text', value: match[0] }] });
          start = match.index! + match[0].length;
        }
        result.push({ type: 'text', value: value.slice(start) });
        return result;
      });
    };
    visit(tree);
  };
  return <div className="lecture-markdown"><Markdown skipHtml
    remarkPlugins={[remarkMath, ...(gfm ? [remarkGfm] : []), citations]}
    rehypePlugins={[[rehypeKatex, { trust: false, maxExpand: 500, maxSize: 10, strict: 'ignore' }]]}
    components={{
      img: () => null,
      a: ({ href, children }) => {
        const source = href?.startsWith('#wf-source-') ? registered.get(href.slice(11)) : undefined;
        if (source) return <button className="lecture-citation" type="button"
          aria-label={`Nguồn ${source.label}, trang ${source.page}`} disabled={!onSource}
          onClick={() => onSource?.(source.page!)}>{children}</button>;
        return href && allowLinks ? <a href={href} target="_blank" rel="noopener noreferrer">{children}</a> : <span>{children}</span>;
      },
    }}>{text}</Markdown></div>;
}

export default memo(LectureMarkdown);
