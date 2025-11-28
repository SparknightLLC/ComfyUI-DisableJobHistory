import threading
import time
import types
from server import PromptServer

prompt_queue = PromptServer.instance.prompt_queue
original_task_done = prompt_queue.task_done


def new_task_done(self, *args, **kwargs):
	# Extract item_id (first positional arg, or fallback to kwargs)
	item_id = args[0] if args else kwargs.get("item_id")
	if not item_id:
		return  # Skip if no ID found

	# Safely extract prompt_id (history key) before original pops it
	with self.mutex:
		prompt = self.currently_running.get(item_id)
		prompt_id = prompt[1] if prompt and len(prompt) > 1 else None

	# Call original
	original_task_done(*args, **kwargs)

	if not prompt_id:
		return  # Skip if no prompt_id found

	def delayed_delete():
		time.sleep(2)  # Adjustable delay in seconds
		with self.mutex:
			self.history.pop(prompt_id, None)
		print(f"Deleted prompt history for ID: {prompt_id}")

	threading.Thread(target=delayed_delete, daemon=True).start()


# Bind the new function as a method on the instance
prompt_queue.task_done = types.MethodType(new_task_done, prompt_queue)

# No nodes defined
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
