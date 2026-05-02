import ollama

def continuous_chat():
    # This list stores the history of the conversation
    messages = [
        {'role': 'system', 'content': 'You are a helpful AI assistant running locally via Ollama.'}
    ]
    
    print("--- Llama 3 Chat Started (Type 'exit' or 'quit' to stop) ---")

    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break

        # Add user message to history
        messages.append({'role': 'user', 'content': user_input})

        print("AI: ", end="", flush=True)
        full_response = ""

        # Stream the response from the model
        stream = ollama.chat(
            model='llama3:8b',
            messages=messages,
            stream=True,
        )

        for chunk in stream:
            content = chunk['message']['content']
            print(content, end='', flush=True)
            full_response += content

        # Add the AI's full response to history for context in the next turn
        messages.append({'role': 'assistant', 'content': full_response})
        print()

if __name__ == "__main__":
    try:
        continuous_chat()
    except KeyboardInterrupt:
        print("\nChat session ended.")