import json
import os

from google import genai

from .tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS

MODEL = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = """You are an inventory assistant for a small hardware warehouse.

You help the user check and update stock by calling the tools available to you.

Rules:
- Always use a tool to answer questions about stock. Never guess or rely on memory.
- Always use a tool to obtain an item's price. Never guess the price.
- When adding stock, if the user did not explicitly provide a unit price, ask for
  the price and do not call add_item yet. Never use zero as a missing price.
- Call add_item only once for each item the user requested after all required
  information is available.
- For cost questions, calculate the subtotal as requested quantity times unit price,
  calculate VAT as subtotal times the VAT percentage divided by 100, and add the
  VAT to the subtotal for the final total.
- A cost calculation must not change the inventory quantity.
- Show the subtotal, VAT amount, and final total.
- If a tool returns an error, explain the problem to the user in plain language.
- Before deleting an item entirely, make sure that is what the user meant.
- Keep your answers short and factual.
- Do not answer any question unrelated to the inventory task.
"""

MAX_STEPS = 5

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def run_agent(user_message, previous_interaction_id=None, verbose=False):
    """Send a message to the agent and run tools until it produces an answer."""

    completed_mutations = set()

    interaction = client.interactions.create(
        model=MODEL,
        input=user_message,
        tools=TOOL_DECLARATIONS,
        system_instruction=SYSTEM_PROMPT,
        previous_interaction_id=previous_interaction_id,
    )

    for _ in range(MAX_STEPS):
        calls = [s for s in interaction.steps if s.type == "function_call"]

        if not calls:
            return interaction.output_text, interaction.id

        results = []
        for call in calls:
            signature = (call.name, json.dumps(call.arguments, sort_keys=True))
            is_mutation = call.name in {"add_item", "remove_stock", "delete_item"}

            if is_mutation and signature in completed_mutations:
                output = {"error": "Duplicate tool call ignored; this inventory change was already completed."}
            else:
                function = TOOL_FUNCTIONS[call.name]
                output = function(**call.arguments)
                if is_mutation and "error" not in output:
                    completed_mutations.add(signature)

            if verbose:
                print(f"  -> {call.name}({call.arguments}) = {output}")

            results.append({
                "type": "function_result",
                "name": call.name,
                "call_id": call.id,
                "result": [{"type": "text", "text": json.dumps(output)}],
            })

        interaction = client.interactions.create(
            model=MODEL,
            input=results,
            tools=TOOL_DECLARATIONS,
            system_instruction=SYSTEM_PROMPT,
            previous_interaction_id=interaction.id,
        )

    return "I got stuck working on that. Please try rephrasing.", interaction.id
