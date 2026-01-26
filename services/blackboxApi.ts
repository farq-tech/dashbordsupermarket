/**
 * Blackbox AI API Integration
 * Service for connecting to Blackbox AI API for automated code generation
 */

interface BlackboxTaskRequest {
  prompt: string;
  repoUrl: string;
  selectedAgent?: 'blackbox' | string;
  selectedModel?: 'blackboxai/blackbox-pro' | string;
}

interface BlackboxTaskResponse {
  taskId?: string;
  status?: string;
  message?: string;
  error?: string;
  [key: string]: any;
}

class BlackboxApi {
  private baseUrl = 'https://cloud.blackbox.ai/api';
  private apiKey: string;

  constructor(apiKey?: string) {
    // Get API key from environment or use provided key
    this.apiKey = apiKey || process.env.BLACKBOX_API_KEY || '';
    
    if (!this.apiKey) {
      console.warn('Blackbox API key not found. Please set BLACKBOX_API_KEY in .env file');
    }
  }

  /**
   * Create a new task in Blackbox AI
   * @param request Task request parameters
   * @returns Task response with taskId and status
   */
  async createTask(request: BlackboxTaskRequest): Promise<BlackboxTaskResponse> {
    if (!this.apiKey) {
      throw new Error('Blackbox API key is required. Set BLACKBOX_API_KEY in .env file');
    }

    try {
      const response = await fetch(`${this.baseUrl}/tasks`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt: request.prompt,
          repoUrl: request.repoUrl,
          selectedAgent: request.selectedAgent || 'blackbox',
          selectedModel: request.selectedModel || 'blackboxai/blackbox-pro'
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(`Blackbox API error: ${response.status} - ${JSON.stringify(errorData)}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error(`Failed to create Blackbox task: ${String(error)}`);
    }
  }

  /**
   * Get task status by taskId
   * @param taskId Task ID from createTask response
   * @returns Task status and results
   */
  async getTaskStatus(taskId: string): Promise<BlackboxTaskResponse> {
    if (!this.apiKey) {
      throw new Error('Blackbox API key is required');
    }

    try {
      const response = await fetch(`${this.baseUrl}/tasks/${taskId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(`Blackbox API error: ${response.status} - ${JSON.stringify(errorData)}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error(`Failed to get task status: ${String(error)}`);
    }
  }
}

// Export singleton instance
export const blackboxApi = new BlackboxApi();

// Export class for custom instances
export { BlackboxApi };

// Export types
export type { BlackboxTaskRequest, BlackboxTaskResponse };
