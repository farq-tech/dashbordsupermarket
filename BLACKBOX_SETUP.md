# Blackbox AI Integration Setup

This project includes integration with Blackbox AI API for automated code generation.

## Setup Instructions

### 1. Configure API Key

Create a `.env` file in the root directory (or copy from `.env.example`):

```env
BLACKBOX_API_KEY=sk-XCjIzfwEGuDnsQRViZtvKg
```

### 2. Install Dependencies (if needed)

The integration uses native `fetch` API. For Node.js environments, you may need:

```bash
npm install node-fetch @types/node-fetch
# or
npm install node-fetch
```

### 3. Usage

#### Basic Usage

```typescript
import { blackboxApi } from './services/blackboxApi';

// Create a task
const response = await blackboxApi.createTask({
  prompt: 'Add Stripe Payment Integration',
  repoUrl: 'https://github.com/yourusername/yourrepo', // ⚠️ SET YOUR REPO
  selectedAgent: 'blackbox',
  selectedModel: 'blackboxai/blackbox-pro'
});

console.log('Task created:', response);
```

#### Check Task Status

```typescript
// Get task status
const status = await blackboxApi.getTaskStatus(response.taskId);
console.log('Task status:', status);
```

### 4. API Methods

#### `createTask(request: BlackboxTaskRequest)`

Creates a new task in Blackbox AI.

**Parameters:**
- `prompt` (string): Description of what you want to generate
- `repoUrl` (string): Your GitHub repository URL
- `selectedAgent` (optional): Agent type (default: 'blackbox')
- `selectedModel` (optional): Model to use (default: 'blackboxai/blackbox-pro')

**Returns:** Promise with task response containing `taskId` and `status`

#### `getTaskStatus(taskId: string)`

Gets the status of a task by its ID.

**Parameters:**
- `taskId` (string): Task ID from createTask response

**Returns:** Promise with task status and results

### 5. Error Handling

The service includes error handling for:
- Missing API key
- Network errors
- API errors (non-200 responses)

Example:

```typescript
try {
  const response = await blackboxApi.createTask({
    prompt: 'Add feature X',
    repoUrl: 'https://github.com/user/repo'
  });
} catch (error) {
  console.error('Failed to create task:', error.message);
}
```

### 6. Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BLACKBOX_API_KEY` | Your Blackbox AI API key | Yes |

### 7. Example Files

See `examples/blackbox-usage.ts` for complete usage examples.

## Notes

- Make sure your GitHub repository is accessible
- The API key is sensitive - never commit it to version control
- Add `.env` to your `.gitignore` file
- The service uses environment variables for security
