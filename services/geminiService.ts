
import { GoogleGenAI, Type } from '@google/genai';
import { ChatMessage } from '../types';

const getGenAI = () => new GoogleGenAI({ apiKey: process.env.API_KEY as string });

export const generateText = async (prompt: string): Promise<string> => {
  try {
    const ai = getGenAI();
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
    });
    return response.text;
  } catch (error) {
    console.error('Gemini API Error (generateText):', error);
    return 'Error generating text. Please check the console for details.';
  }
};

export const analyzeComplexTask = async (taskDescription: string): Promise<string> => {
  try {
    const ai = getGenAI();
    const prompt = `
      You are an expert system operator for a "Production Control Plane" (PCP).
      Your task is to analyze a user's natural language request and convert it into a structured JSON object representing a sequence of commands for the PCP.
      
      Available commands and their parameters are:
      - SCAN_SITE: { domain: string }
      - PUBLISH_REPORT: { client: string, dataset: string, format: 'pdf' | 'html' }
      - START_CAMPAIGN: { channel: 'linkedin' | 'meta', campaign_id: string }
      - REVERT_ACTION: { action_id: string, reason: string }

      User Request: "${taskDescription}"

      Based on the request, determine the necessary command(s). Provide your response as a JSON object with a "commands" array. Each object in the array should have "command_type" and "params". If you cannot determine the commands, return an empty array and provide a reason in the "reason" field.
    `;

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-pro',
      contents: prompt,
      config: { 
        thinkingConfig: { thinkingBudget: 32768 },
        responseMimeType: 'application/json',
      },
    });

    return response.text;
  } catch (error) {
    console.error('Gemini API Error (analyzeComplexTask):', error);
    return JSON.stringify({ error: 'Failed to analyze task. Please check the console.' });
  }
};

export const continueChat = async (history: ChatMessage[]): Promise<string> => {
  try {
    const ai = getGenAI();
    const chat = ai.chats.create({
      model: 'gemini-2.5-flash',
      config: {
        systemInstruction: `You are a helpful assistant for a Production Control Plane (PCP) dashboard. Your name is 'PCP-Bot'. You are knowledgeable about the system's components like the Orchestrator, Command Poller, Action Ledger, and available commands (SCAN_SITE, PUBLISH_REPORT, etc.). Be concise and helpful.`,
      },
    });

    // The user's message is the last one in the history
    const lastMessage = history[history.length - 1];

    // Note: The current SDK doesn't directly support passing history in this simplified way.
    // For a real app, you'd manage history and pass it to sendMessage.
    // Here we'll just send the last message for simplicity.
    const response = await chat.sendMessage({ message: lastMessage.text });
    return response.text;

  } catch (error) {
    console.error('Gemini API Error (continueChat):', error);
    return 'Sorry, I encountered an error. Please try again.';
  }
};

export const groundedSearch = async (query: string): Promise<{ answer: string; sources: any[] }> => {
  try {
    const ai = getGenAI();
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: `Answer the following question based on real-time information from the web: ${query}`,
      config: {
        tools: [{ googleSearch: {} }],
      },
    });
    
    const answer = response.text;
    const sources = response.candidates?.[0]?.groundingMetadata?.groundingChunks || [];
    
    return { answer, sources };
  } catch (error) {
    console.error('Gemini API Error (groundedSearch):', error);
    return {
      answer: 'Error performing grounded search. Please check the console.',
      sources: []
    };
  }
};
