# Local Linked Art guidance

This directory vendors the unmodified Linked Art recommended-vocabulary page
and its CC BY 4.0 license from revision
`bcbff1761e65f44eeaeb92b4b2b83da2783539f8` of
[linked-art/linked.art](https://github.com/linked-art/linked.art).
Credit: Linked Art contributors. The manifest records original paths, immutable
source URLs, and SHA-256 checksums. No endorsement is implied.

`scripts/build_category_eval.py` extracts the Sculpture, Painting, Drawing,
Print, Furniture, and Architecture entries under **Object Types**. It expands
the AAT identifiers to full URIs and embeds the names and descriptions verbatim
in the MAP + Linked Art prompt. The Met classification lists and operational
rules are local workshop policy; they are not supplied by Linked Art.

This is a documentation subset, not a checkout of the website or a schema/JSON-LD
export pipeline. Relative links and website formatting are preserved in the
upstream file. The agent receives the selected text directly in its prompt; it
does not browse the web, resolve URIs, or read arbitrary repository files.
