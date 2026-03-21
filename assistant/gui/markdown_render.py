"""Markdown to styled HTML converter for chat message rendering."""

import html
import re


# Dark-themed CSS for rendered message content.
MESSAGE_CSS = """
<style>
body {
	font-family: 'Segoe UI', 'Inter', sans-serif;
	font-size: 13px;
	color: #E2E8F0;
	line-height: 1.65;
	margin: 0;
	padding: 0;
	background: transparent;
}
p { margin: 4px 0; }
strong, b { color: #F1F5F9; font-weight: 700; }
em, i { font-style: italic; }
a { color: #60A5FA; text-decoration: none; }
a:hover { text-decoration: underline; }
ul, ol { margin: 6px 0; padding-left: 20px; }
li { margin: 2px 0; }
code {
	background: #334155;
	color: #A5F3FC;
	padding: 1px 5px;
	border-radius: 4px;
	font-family: 'Cascadia Code', 'Consolas', 'Fira Code', monospace;
	font-size: 12px;
}
pre {
	background: #0F172A;
	border: 1px solid #334155;
	border-radius: 8px;
	padding: 12px 14px;
	margin: 8px 0;
	overflow-x: auto;
	position: relative;
}
pre code {
	background: transparent;
	color: #E2E8F0;
	padding: 0;
	font-size: 12px;
	line-height: 1.5;
}
.code-header {
	display: flex;
	justify-content: space-between;
	background: #1E293B;
	border: 1px solid #334155;
	border-bottom: none;
	border-radius: 8px 8px 0 0;
	padding: 6px 12px;
	margin-top: 8px;
	font-size: 11px;
	color: #94A3B8;
	font-family: 'Segoe UI', sans-serif;
}
.code-header + pre {
	margin-top: 0;
	border-top-left-radius: 0;
	border-top-right-radius: 0;
}
blockquote {
	border-left: 3px solid #3B82F6;
	margin: 8px 0;
	padding: 4px 12px;
	color: #94A3B8;
	background: rgba(59, 130, 246, 0.05);
	border-radius: 0 6px 6px 0;
}
hr {
	border: none;
	border-top: 1px solid #334155;
	margin: 12px 0;
}
table {
	border-collapse: collapse;
	width: 100%;
	margin: 8px 0;
}
th, td {
	border: 1px solid #334155;
	padding: 6px 10px;
	text-align: left;
	font-size: 12px;
}
th {
	background: #1E293B;
	color: #F1F5F9;
	font-weight: 600;
}
</style>
"""


def markdown_to_html(text: str) -> str:
	"""Convert markdown text to styled HTML for display in QTextBrowser."""
	if not text:
		return ""

	# Process code blocks first (``` ... ```) to avoid interfering with inline rules.
	text = _process_code_blocks(text)

	# Process inline elements.
	lines = text.split("\n")
	html_lines = []
	in_list = False
	list_type = ""

	for line in lines:
		stripped = line.strip()

		# Skip lines that were already processed as code blocks.
		if stripped.startswith("<div class=") or stripped.startswith("<pre") or stripped.startswith("</"):
			html_lines.append(line)
			continue

		# Headers.
		header_match = re.match(r"^(#{1,6})\s+(.*)", stripped)
		if header_match:
			level = len(header_match.group(1))
			content = _process_inline(header_match.group(2))
			sizes = {1: "18px", 2: "16px", 3: "14px", 4: "13px", 5: "12px", 6: "11px"}
			html_lines.append(
				f'<p style="font-size:{sizes.get(level, "13px")};font-weight:700;'
				f'color:#F1F5F9;margin:10px 0 4px 0;">{content}</p>'
			)
			continue

		# Horizontal rule.
		if re.match(r"^[-*_]{3,}\s*$", stripped):
			html_lines.append("<hr>")
			continue

		# Blockquote.
		if stripped.startswith(">"):
			content = _process_inline(stripped.lstrip("> "))
			html_lines.append(f"<blockquote>{content}</blockquote>")
			continue

		# Unordered list items.
		ul_match = re.match(r"^[-*+]\s+(.*)", stripped)
		if ul_match:
			if not in_list or list_type != "ul":
				if in_list:
					html_lines.append(f"</{list_type}>")
				html_lines.append("<ul>")
				in_list = True
				list_type = "ul"
			html_lines.append(f"<li>{_process_inline(ul_match.group(1))}</li>")
			continue

		# Ordered list items.
		ol_match = re.match(r"^\d+\.\s+(.*)", stripped)
		if ol_match:
			if not in_list or list_type != "ol":
				if in_list:
					html_lines.append(f"</{list_type}>")
				html_lines.append("<ol>")
				in_list = True
				list_type = "ol"
			html_lines.append(f"<li>{_process_inline(ol_match.group(1))}</li>")
			continue

		# Close any open list.
		if in_list:
			html_lines.append(f"</{list_type}>")
			in_list = False
			list_type = ""

		# Empty line = paragraph break.
		if not stripped:
			html_lines.append("<br>")
			continue

		# Regular paragraph.
		html_lines.append(f"<p>{_process_inline(stripped)}</p>")

	if in_list:
		html_lines.append(f"</{list_type}>")

	body = "\n".join(html_lines)
	return f"{MESSAGE_CSS}<body>{body}</body>"


def _process_code_blocks(text: str) -> str:
	"""Replace fenced code blocks with styled HTML pre/code elements."""

	def _replace_block(match):
		lang = match.group(1) or ""
		code = html.escape(match.group(2).strip())
		header = ""
		if lang:
			header = f'<div class="code-header"><span>{lang}</span></div>'
		return f"{header}<pre><code>{code}</code></pre>"

	return re.sub(r"```(\w*)\n(.*?)```", _replace_block, text, flags=re.DOTALL)


def _process_inline(text: str) -> str:
	"""Apply inline markdown formatting: bold, italic, code, links."""
	# Inline code (must be before bold/italic to avoid conflicts).
	text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
	# Bold + italic.
	text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
	# Bold.
	text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
	# Italic.
	text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
	# Links.
	text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
	return text
