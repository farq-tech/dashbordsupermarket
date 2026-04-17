# What You Can Do with Blackbox MCP

The Blackbox MCP (Model Context Protocol) server provides AI-powered code generation and automation capabilities directly within Cursor. Here's what you can do:

## 🚀 Core Capabilities

### 1. **Automated Code Generation**
- Generate complete features from natural language prompts
- Create entire components, functions, or modules
- Automatically implement integrations (e.g., Stripe, payment systems)
- Generate boilerplate code and project scaffolding

### 2. **Code Modification & Refactoring**
- Refactor existing code based on descriptions
- Update code to follow best practices
- Migrate code between frameworks or versions
- Optimize performance and fix bugs

### 3. **Repository-Based Development**
- Work directly with your GitHub repositories
- Make changes across multiple files
- Create pull requests automatically
- Generate commits with meaningful messages

## 🛠️ Available Operations

### Through MCP Tools (when connected):

1. **Create Tasks**
   - Submit code generation requests
   - Specify what you want to build
   - Set target repository and branch

2. **Monitor Task Status**
   - Check progress of code generation
   - Get real-time updates
   - Retrieve generated code

3. **Code Analysis**
   - Analyze codebase structure
   - Understand dependencies
   - Generate documentation

4. **Automated Testing**
   - Generate test files
   - Create unit tests
   - Set up integration tests

## 💡 Practical Use Cases for Your Fustog Project

### 1. **Add Payment Integration**
```
"Add Stripe payment processing to the checkout flow"
```

### 2. **Implement New Features**
```
"Add user authentication with JWT tokens"
"Create an admin dashboard for managing products"
"Add product search and filtering functionality"
```

### 3. **Enhance Existing Features**
```
"Improve the cart drawer with better animations"
"Add product recommendations based on cart items"
"Implement order tracking functionality"
```

### 4. **Code Quality Improvements**
```
"Refactor the API hooks to use React Query"
"Add TypeScript types for all API responses"
"Implement error boundaries for better error handling"
```

### 5. **Testing & Documentation**
```
"Generate unit tests for all React components"
"Create API documentation using OpenAPI"
"Add Storybook stories for all UI components"
```

## 📋 How to Use Blackbox MCP

### Option 1: Through Cursor's MCP Interface
Once the MCP server is connected and Cursor is restarted:
1. Open Cursor's MCP tools panel
2. Select "blackbox" server
3. Choose the tool you want to use
4. Provide your prompt and repository URL

### Option 2: Through Code (Direct API)
Use the `blackboxApi` service we created:

```typescript
import { blackboxApi } from './services/blackboxApi';

// Create a task
const task = await blackboxApi.createTask({
  prompt: 'Add user authentication system',
  repoUrl: 'https://github.com/abdulrhman-farq/fustog',
  selectedAgent: 'blackbox',
  selectedModel: 'blackboxai/blackbox-pro'
});

// Check status
const status = await blackboxApi.getTaskStatus(task.taskId);
```

### Option 3: Through Cursor Chat
Simply ask in Cursor's chat:
- "Use Blackbox to add Stripe payment integration"
- "Generate a user profile component using Blackbox"
- "Refactor the cart logic with Blackbox"

## 🎯 Example Prompts for Your Project

### E-commerce Features
- "Add product reviews and ratings system"
- "Implement wishlist functionality"
- "Create a product comparison feature"
- "Add multi-language support (i18n)"
- "Implement dark mode toggle"

### Backend/API
- "Create REST API endpoints for orders"
- "Add database models for user preferences"
- "Implement caching layer for product data"
- "Create webhook handlers for payment notifications"

### UI/UX Improvements
- "Add loading skeletons for all async components"
- "Implement infinite scroll for products"
- "Create mobile-optimized navigation menu"
- "Add smooth page transitions"

### DevOps & Infrastructure
- "Set up CI/CD pipeline with GitHub Actions"
- "Create Docker configuration for the app"
- "Add environment variable management"
- "Set up monitoring and error tracking"

## ⚙️ Configuration

Your Blackbox MCP is configured with:
- **API Endpoint**: `https://cloud.blackbox.ai/api/mcp`
- **API Key**: Configured in `.env` file
- **Transport**: HTTP
- **Model**: `blackboxai/blackbox-pro` (default)

## 🔍 Checking Available Tools

To see what tools are available, you can:

1. **List MCP Resources** (in Cursor):
   ```typescript
   // This will show available resources when MCP is connected
   list_mcp_resources({ server: "blackbox" })
   ```

2. **Check Tool Descriptors**:
   Tools are typically stored in:
   ```
   C:\Users\abdul\.cursor\projects\f-fustog\mcps\blackbox\tools\
   ```

3. **Use Cursor's MCP Panel**:
   - Open Cursor settings
   - Navigate to MCP servers
   - Check available tools for "blackbox"

## 🚨 Troubleshooting

If MCP tools aren't showing up:

1. **Restart Cursor** - MCP servers load on startup
2. **Check Connection** - Verify the API key is correct
3. **Check Logs** - Look for MCP connection errors in Cursor logs
4. **Verify Configuration** - Ensure `SERVER_METADATA.json` is correct

## 📚 Next Steps

1. **Restart Cursor** to load the MCP server
2. **Test the connection** by listing available tools
3. **Try a simple task** like "Add a README file"
4. **Explore available tools** through Cursor's MCP interface

## 💻 Integration with Your Codebase

You can also use Blackbox programmatically in your code:

```typescript
// In your React components or API routes
import { blackboxApi } from '../services/blackboxApi';

// Example: Auto-generate code on button click
const handleGenerateFeature = async () => {
  const result = await blackboxApi.createTask({
    prompt: 'Add product search with autocomplete',
    repoUrl: 'https://github.com/abdulrhman-farq/fustog'
  });
  console.log('Task created:', result);
};
```

---

**Note**: The MCP server needs to be fully connected and Cursor restarted for MCP tools to appear. Until then, you can use the direct API integration we've set up in `services/blackboxApi.ts`.
