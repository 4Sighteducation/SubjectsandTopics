# SubjectsandTopics

A tool for generating and managing standardized curriculum topic lists for various exam boards, exam types, and subjects.

## Overview

SubjectsandTopics is designed to solve the problem of obtaining comprehensive, structured curriculum topic lists for use in educational applications. It generates these lists via the Anthropic AI API (Claude) and organizes them for easy import into databases like Knack.

Key features:
- Generate topic lists for any exam board, type, and subject combination
- Use Anthropic's Claude AI model for accurate curriculum extraction
- Export in JSON or CSV format for database import
- Assign unique identifiers to collections and individual topics
- Provide a simple web interface for topic management

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- OpenRouter API key (for Anthropic Claude access)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/4Sighteducation/SubjectsandTopics.git
cd SubjectsandTopics
```

2. Install dependencies:
```bash
npm install
```

3. Create an `.env` file based on the example:
```bash
cp .env.example .env
```

4. Add your OpenRouter API key to the `.env` file:
```
OPENROUTER_API_KEY=your_api_key_here
```

5. Start the application:
```bash
npm start
```

## Usage

1. Open your browser to `http://localhost:3000`
2. Select an exam board, exam type, and subject
3. Click "Generate Topics"
4. Review the generated topics
5. Export to JSON or CSV

## Data Format

Topics are structured as follows:

```json
{
  "id": "aqa-alevel-physics-2025-01",
  "examBoard": "AQA",
  "examType": "A-Level",
  "subject": "Physics",
  "version": "2025.1",
  "topics": [
    {
      "id": "1.1",
      "uuid": "t-aqa-alev-phy-1-1-abc123",
      "topic": "Mechanics: Forces and Motion",
      "mainTopic": "Mechanics",
      "subtopic": "Forces and Motion"
    },
    // more topics...
  ]
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built for VESPA Flashcards
- Uses Anthropic's Claude AI model via OpenRouter
