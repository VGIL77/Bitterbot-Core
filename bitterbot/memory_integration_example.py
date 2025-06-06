"""
Example integration of BitterBot Memory System with main orchestrator
"""

from memory import BitterBotMemory

class BitterBotOrchestrator:
    """Example orchestrator with memory integration"""
    
    def __init__(self):
        # Initialize memory system
        self.memory = BitterBotMemory()
        
        # Other components would be initialized here
        # self.llm = ...
        # self.tools = ...
        
    async def process_message(self, user_id: str, message: str):
        """Process a user message with memory context"""
        
        # 1. Retrieve relevant context from memory
        context = await self.memory.retrieve_context(message, k=5)
        
        # 2. Generate response with context
        # In real implementation, this would use your LLM
        response = await self.generate_response(message, context)
        
        # 3. Store the interaction in memory
        await self.memory.store_interaction(
            prompt=message,
            response=response,
            metadata={
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return response
        
    async def generate_response(self, message: str, context: list) -> str:
        """Generate response using LLM with context"""
        # TODO: Integrate with actual LLM
        # This is a placeholder
        return f"Response to: {message} (with {len(context)} context items)"
        
    async def start_dream_cycle(self):
        """Start the dream engine for idle-time learning"""
        # TODO: Initialize and start dream cycle
        print("💭 Dream cycle would start here...")

# Example usage
if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    
    async def main():
        # Initialize orchestrator
        bot = BitterBotOrchestrator()
        
        # Example interaction
        user_id = "example_user"
        message = "Tell me about quantum computing"
        
        print(f"User: {message}")
        response = await bot.process_message(user_id, message)
        print(f"BitterBot: {response}")
        
    # Run example
    asyncio.run(main())