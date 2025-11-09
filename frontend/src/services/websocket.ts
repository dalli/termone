export class WebSocketClient {
  private url: string;
  private ws: WebSocket | null = null;
  private handlers: Map<string, (data: any) => void> = new Map();

  constructor(url: string) {
    this.url = url;
  }

  connect() {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        this.ws.onopen = () => resolve(this);
        this.ws.onerror = (error) => reject(error);
        this.ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          this.handlers.forEach((handler) => handler(data));
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  on(event: string, handler: (data: any) => void) {
    this.handlers.set(event, handler);
  }

  close() {
    if (this.ws) {
      this.ws.close();
    }
  }
}
