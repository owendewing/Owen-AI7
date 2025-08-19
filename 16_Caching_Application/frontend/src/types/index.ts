export interface ChatResponse {
  response: string;
  tool_used: string;
  cached: boolean;
  session_id: string;
  userMessage?: string;
  timestamp?: string;
}

export interface DocumentUploadResponse {
  message: string;
  documents_processed: number;
} 