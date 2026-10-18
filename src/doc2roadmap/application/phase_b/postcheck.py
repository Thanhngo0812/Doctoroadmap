"""Sentence-level source checks shared by assistant answers and documents."""
import re
import unicodedata

from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter


REF = re.compile(r'\[([A-Z]+\d+)\]')
COMPOUND = re.compile(r'\[((?:[A-Z]+\d+\s*[,;]\s*)+[A-Z]+\d+)\]')
FORMULA = re.compile(r'[=∑∫√]|\\(?:frac|sum|int|begin)\b|\$\$')
POSTCHECK_VERSION = 'sentence-postcheck-1'


def _names(graph):
    names = set()
    for node in graph.nodes.values():
        values = [node.get('display_name'), node.get('name'), *node.get('aliases', [])]
        for value in values:
            if isinstance(value, dict):
                value = value.get('name')
            if value:
                names.add(' '.join(unicodedata.normalize('NFC', str(value)).casefold().split()))
    return sorted(names, key=len, reverse=True)


def _name_pattern(name):
    return r'(?<!\w)' + r'\s+'.join(re.escape(part) for part in name.split()) + r'(?!\w)'


def _contains_name(text, names):
    return any(re.search(_name_pattern(name), text) for name in names)


def _outside_allowed(body, names):
    text = unicodedata.normalize('NFC', body).casefold()
    if FORMULA.search(body) or re.search(r'định nghĩa|công thức|(?:theo|trong)\s+(?:sách|tài liệu|giáo trình)', text):
        return False
    for name in names:
        if re.search(_name_pattern(name) + r'(?:\s*\([^()]*\))?\s+(?:là|nghĩa là|được gọi là)\b', text):
            return False
    if _contains_name(text, names) and re.search(r'\b(?:được gọi là|nghĩa là)\b', text):
        return False
    return True


def check_text(text, *, graph, settings, citations_by_label=None, outside_blocks=()):
    names = _names(graph)
    splitter = UnicodeSentenceSplitter()
    citations, warnings, blocks = {}, [], list(outside_blocks)
    counts = {'unsourced_sentence': 0, 'labels_removed': 0,
              'outside_blocks_removed': 0, 'sourced_sentences': 0}

    def extract(match):
        blocks.append(match[1].strip())
        return ''

    text = re.sub(r':::outside_document\s*\n(.*?)\n:::', extract, text, flags=re.S)
    text = COMPOUND.sub(lambda match: ''.join('[' + label.strip() + ']'
        for label in re.split(r'[,;]', match[1])), text)
    kept_lines = []
    for line in text.splitlines():
        if not line.strip():
            kept_lines.append('')
            continue
        # Retain structural headings, but check claims formatted as headings too.
        heading = re.match(r'^\s*#{1,6}\s+(.+)', line)
        if heading:
            title = re.sub(r'^\d+(?:\.\d+)*[.)]?\s+', '', heading[1]).casefold()
            if (not REF.search(title) and not re.search(r'\d|\b(?:là|có|gồm|được|nghĩa là)\b', title)
                    and not title.endswith(('.', '!', '?', '…'))):
                kept_lines.append(line.strip())
                continue
        # A suffix citation after punctuation belongs to the preceding sentence.
        line = re.sub(r'([.!?…])\s+((?:\[[A-Z]+\d+\]\s*)+)',
            lambda match: ' ' + match[2].strip() + match[1] + ' ', line)
        accepted = []
        for span in splitter.split(line):
            sentence = line[span.start:span.end].strip()
            if FORMULA.search(sentence):
                warnings.append({'kind': 'generated_formula'})
                continue
            labels = REF.findall(sentence)
            known, removed = {}, []
            formulas = getattr(graph, 'answer_formulas', {}) if citations_by_label is None else {}
            for label in labels:
                if label in formulas:
                    known[label] = None
                    continue
                if citations_by_label is not None:
                    citation = citations_by_label.get(label)
                else:
                    source = graph.sources.resolve(label)
                    citation = None
                    if source:
                        quote = source.get('quote')
                        if not quote:
                            source_text = source['source_text']
                            candidates = [source_text[s.start:s.end] for s in splitter.split(source_text)] or [source_text]
                            words = set(re.findall(r'\w+', sentence.casefold()))
                            quote = max(candidates, key=lambda row: len(words & set(re.findall(r'\w+', row.casefold()))))
                        citation = graph.sources.citation(label, quote)
                if citation:
                    known[label] = citation
                else:
                    removed.append(label)
            if removed:
                counts['labels_removed'] += len(removed)
                warnings.append({'kind': 'unknown_label', 'labels': removed})
            sentence = REF.sub(lambda match: match[0] if match[1] in known else '', sentence).strip()
            plain = unicodedata.normalize('NFC', sentence).casefold()
            connector = (not labels and len(sentence) <= settings.connector_sentence_max_chars
                and not re.search(r'\d|[+*/^<>≤≥±−]', sentence)
                and not _contains_name(plain, names) and sentence.endswith(('.', '!', '?', '…')))
            if not known and not connector:
                if sentence:
                    counts['unsourced_sentence'] += 1
                    warnings.append({'kind': 'unsourced_sentence'})
                continue
            if known:
                counts['sourced_sentences'] += 1
                citations.update({label: value for label, value in known.items() if value is not None})
            accepted.append(sentence)
        if accepted:
            kept_lines.append(' '.join(accepted))
    outside = []
    for body in blocks:
        body = str(body).strip()
        if (not settings.allow_outside_examples or outside or not _outside_allowed(body, names)
                or not counts['sourced_sentences']):
            counts['outside_blocks_removed'] += 1
            warnings.append({'kind': 'outside_document_removed'})
        else:
            outside.append(REF.sub('', body).strip())
    return {'text': '\n'.join(kept_lines).strip(), 'citations': list(citations.values()),
            'warnings': warnings, 'counts': counts, 'outside_blocks': outside}
