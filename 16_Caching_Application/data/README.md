# Python Documentation Data

This directory contains Python documentation files that will be ingested into the vectorstore for RAG (Retrieval-Augmented Generation).

## Supported File Types

- `.md` - Markdown files
- `.txt` - Plain text files
- `.pdf` - PDF files (newly added support!)

## How to Add Documentation

1. Place your Python documentation files in this directory
2. You can organize them in subdirectories
3. The system will automatically process all `.md`, `.txt`, and `.pdf` files recursively

## Example Structure

```
data/
├── python_basics/
│   ├── variables.md
│   ├── functions.md
│   └── classes.md
├── libraries/
│   ├── pandas.md
│   ├── numpy.md
│   └── matplotlib.md
├── official_docs/
│   ├── built_in_functions.pdf
│   └── standard_library.pdf
└── advanced/
    ├── decorators.md
    ├── generators.md
    └── async_await.md
```

## After Adding Files

1. Restart the application or call the `/upload-documents` endpoint
2. The system will automatically chunk and embed your documentation
3. Your documentation will be available for RAG queries

## Tips

- Use clear, descriptive filenames
- Include code examples in your documentation
- Structure your content with headers for better chunking
- Keep individual files focused on specific topics
- PDF files will be processed page by page 