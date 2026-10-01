# Node.js tutorials: Fastify and Temporal

Three practical guides (PDF), built from code that is type-checked, tested and run.

| Guide | Pages | Companion code |
|---|---|---|
| [Fastify with Node.js – The Complete Practical Tutorial](pdfs/Fastify_NodeJS_Complete_Tutorial.pdf) | 79 | [fastify-tasks-api](https://github.com/tcsr/fastify-tasks-api), [fastify-examples](https://github.com/tcsr/fastify-examples) |
| [Temporal with Node.js – The Complete Practical Tutorial](pdfs/Temporal_NodeJS_Complete_Tutorial.pdf) | 78 | [temporal-order-service](https://github.com/tcsr/temporal-order-service), [temporal-examples](https://github.com/tcsr/temporal-examples) |
| [Fastify + Temporal – Durable HTTP APIs](pdfs/Fastify_Temporal_Companion_Guide.pdf) | 20 | [fastify-temporal-orders](https://github.com/tcsr/fastify-temporal-orders) |

Verified with Node.js 24, Fastify 5.12, @temporalio/* 1.24, TypeScript 7 (September 2026).

## How the PDFs are built

The builders in `builders/` generate the PDFs with ReportLab. Code listings are
**read from the companion repositories at build time**, so the PDFs always show the
exact, tested code:

- `highlight.py` – syntax highlighting (Pygments)
- `annotate.py` – splits listings into chunks with numbered callouts
- `callouts*.py` – the callout notes; each is anchored to an exact line of code and the
  build fails if a line it refers to no longer exists
- `*_content.py` – chapter content for the real-world examples and the combined guide

## Rebuilding

Clone the companion repositories next to this one:

```bash
git clone https://github.com/tcsr/nodejs-tutorials
git clone https://github.com/tcsr/fastify-temporal-orders
git clone https://github.com/tcsr/temporal-examples
git clone https://github.com/tcsr/fastify-examples
pip install -r nodejs-tutorials/requirements.txt
cd nodejs-tutorials
python builders/build_fastify_tutorial.py
python builders/build_temporal_tutorial.py
python builders/build_combined_tutorial.py
```

The output goes to `pdfs/`. Set `PROJECTS_DIR` if the companion repositories live
somewhere else.
