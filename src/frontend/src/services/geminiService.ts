import { GoogleGenAI, GenerateContentResponse } from "@google/genai";
import { Message } from "../types.ts";

// Initialize the client
const apiKey = process.env.API_KEY || ''; 
const ai = new GoogleGenAI({ apiKey });

const MODEL_NAME = 'gemini-2.5-flash';
// Fixed: Thinking budget reduced to 16384. Max for gemini-2.5-flash is 24576.
const THINKING_CONFIG = { thinkingBudget: 16384 };

/**
 * Simulates SQL generation based on natural language.
 * In a real app, this would return SQL to be executed by the backend.
 */
export const generateSQL = async (
  nlQuery: string, 
  schemaContext: string
): Promise<{ sql: string; explanation: string }> => {
  if (!apiKey) {
    // Fallback for demo without API key
    return {
      sql: "SELECT * FROM users WHERE active = 1;",
      explanation: "（演示模式）这是基于您的请求生成的模拟SQL语句。"
    };
  }

  try {
    const prompt = `
      You are a database expert.
      Schema Context: ${schemaContext}
      User Question: ${nlQuery}
      
      Generate a valid SQL query for MySQL. 
      Also provide a brief explanation in Chinese.
      Return ONLY JSON format: { "sql": "...", "explanation": "..." }
    `;

    const response: GenerateContentResponse = await ai.models.generateContent({
      model: MODEL_NAME,
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        thinkingConfig: THINKING_CONFIG
      }
    });

    const text = response.text;
    if (!text) throw new Error("No response from AI");
    
    return JSON.parse(text);
  } catch (error) {
    console.error("Gemini API Error:", error);
    return {
      sql: "-- Error generating SQL",
      explanation: "无法生成SQL，请检查API Key或网络连接。"
    };
  }
};

/**
 * Summarizes query results into natural language.
 */
export const summarizeData = async (
  data: any[], 
  userQuery: string
): Promise<string> => {
  if (!apiKey) return "（演示模式）数据查询成功，结果显示了符合条件的前10项记录。";

  try {
    const prompt = `
      User Query: ${userQuery}
      Data Result (JSON): ${JSON.stringify(data.slice(0, 5))}... (truncated)
      
      Summarize this data result in Chinese for a non-technical user in 1-2 sentences.
    `;

    const response: GenerateContentResponse = await ai.models.generateContent({
      model: MODEL_NAME,
      contents: prompt,
      // Summarization is simpler, but we stick to the requested model. 
      // Thinking budget can be lower or default here, but sticking to instructions.
      config: {
        thinkingConfig: THINKING_CONFIG 
      }
    });

    return response.text || "分析完成。";
  } catch (error) {
    return "无法生成数据摘要。";
  }
};

/**
 * Generates a database schema and analysis from a project description.
 * Returns a structured object with analysis and ddl.
 */
export const generateSchema = async (description: string): Promise<{ analysis: string; ddl: string }> => {
  if (!apiKey) {
    return {
      analysis: "根据您的描述，我们识别出系统核心实体为用户、商品和订单。我们将采用第三范式进行设计，确保数据冗余最小化。\n\n1. 用户表：存储基本信息。\n2. 商品表：包含价格、库存。\n3. 订单表：关联用户，作为主表。\n4. 订单明细表：关联订单与商品，解决多对多关系。",
      ddl: "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(255));\nCREATE TABLE products (id INT PRIMARY KEY, price DECIMAL(10,2));"
    };
  }

  try {
    const prompt = `
      You are a senior database architect.
      Analyze the following business requirement and design a MySQL database schema (DDL) in 3NF.
      
      Requirement: "${description}"
      
      Return a JSON object with two fields:
      1. "analysis": A detailed explanation of the schema design, entities, and relationships in Chinese (Markdown supported).
      2. "ddl": The raw SQL DDL statements to create the tables.
      
      Response Format: JSON
    `;

    const response: GenerateContentResponse = await ai.models.generateContent({
      model: MODEL_NAME,
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        thinkingConfig: THINKING_CONFIG
      }
    });

    const text = response.text || "{}";
    return JSON.parse(text);
  } catch (error) {
    console.error(error);
    throw new Error("Failed to generate schema");
  }
};