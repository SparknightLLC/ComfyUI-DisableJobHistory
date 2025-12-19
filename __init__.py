import threading
import time
import types
from server import PromptServer

prompt_queue = PromptServer.instance.prompt_queue
original_task_done = prompt_queue.task_done


def new_task_done(self, *args, **kwargs):
	# Always call the original, no matter what, to avoid "unfinished" queue state.
	# But try to capture prompt_id first (while currently_running still has it).
	item_id = None
	prompt_id = None

	if args:
		item_id = args[0]
	else:
		item_id = kwargs.get("item_id")

	if item_id is not None:
		with self.mutex:
			prompt = self.currently_running.get(item_id)
			# ComfyUI commonly stores prompt_id at index 1 in the running item tuple/list.
			prompt_id = prompt[1] if prompt and len(prompt) > 1 else None

	# IMPORTANT: always execute the real task_done
	original_task_done(*args, **kwargs)

	if not prompt_id:
		return

	def delayed_delete():
		# Give the frontend a chance to fetch /history/{prompt_id} if it does that on completion.
		time.sleep(5)  # try increasing delay if you see phantom entry

		with self.mutex:
			self.history.pop(prompt_id, None)
			print(f"Deleted prompt history for ID: {prompt_id}")

		# Nudge clients to refresh queue/history state (prevents “stale UI” phantom entries)
		try:
			self.server.queue_updated()
		except Exception:
			pass

	threading.Thread(target=delayed_delete, daemon=True).start()


prompt_queue.task_done = types.MethodType(new_task_done, prompt_queue)

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
