/**
 * Example usage of Blackbox AI API integration
 * 
 * Make sure to:
 * 1. Set BLACKBOX_API_KEY in your .env file
 * 2. Update the repoUrl to your actual GitHub repository
 */

import { blackboxApi } from '../services/blackboxApi';

async function exampleCreateTask() {
  try {
    // Create a new task
    const response = await blackboxApi.createTask({
      prompt: 'Add Stripe Payment Integration',
      repoUrl: 'https://github.com/user/repo', // ⚠️ SET YOUR REPO URL HERE
      selectedAgent: 'blackbox',
      selectedModel: 'blackboxai/blackbox-pro'
    });

    console.log('Task created:', response);
    
    // If taskId is returned, you can check status
    if (response.taskId) {
      console.log('Task ID:', response.taskId);
      
      // Poll for task status (example)
      // const status = await blackboxApi.getTaskStatus(response.taskId);
      // console.log('Task status:', status);
    }
  } catch (error) {
    console.error('Error creating task:', error);
  }
}

// Example: Check task status
async function exampleCheckStatus(taskId: string) {
  try {
    const status = await blackboxApi.getTaskStatus(taskId);
    console.log('Task status:', status);
  } catch (error) {
    console.error('Error checking status:', error);
  }
}

// Uncomment to run examples:
// exampleCreateTask();
// exampleCheckStatus('your-task-id-here');

export { exampleCreateTask, exampleCheckStatus };
