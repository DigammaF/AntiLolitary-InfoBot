
import praw
import prawcore

from json import dumps, loads
from pathlib import Path
from time import time
from itertools import chain

from bot import bot

class ProtectedUsers:

	file_path = Path("protected_users.txt")

	def __init__(self, users):

		self.users = users

	def save(self):

		with open(self.file_path, "w", encoding="utf-8") as f:
			f.write(dumps(list(self.users), indent=4))

	@classmethod
	def load(cls):

		if cls.file_path.exists():
			with open(cls.file_path, "r", encoding="utf-8") as f:
				return cls(users=set(loads(f.read())))

		else:
			return cls(users=set())

	def __enter__(self):
		return self

	def __exit__(self, *args, **kwargs):
		self.save()

	def add(self, user):
		self.users.add(user)

	def __contains__(self, user):
		return user in self.users

	def __iter__(self):
		return (e for e in self.users)

def collect_protected_users(bot, protected_users):

	print("scanning for users to protect...")
	start_time = time()

	if bot.subreddit("antilolitary").user_is_banned:
		print("oh no! bot is banned x-x")
		return

	for obj in chain(bot.subreddit("antilolitary").new(), bot.subreddit("antilolitary").comments()):

		if obj.author.name not in protected_users:
			print(f" adding {obj.author.name}")
			protected_users.add(obj.author.name)

	print(f"done in {time() - start_time:.2f} sec")

def is_comment_propaganda(text):

	return all(word in text for word in ("warning", "active", "antilolitary", "pedophile"))

def counter_propaganda(bot, protected_users):

	print("scanning for propaganda...")
	start_time = time()
	comments_checked = 0

	for user in protected_users:
		
		redditor = praw.models.Redditor(bot, user)

		try:
			for comment in redditor.comments.all():
				for reply in comment.replies:
					comments_checked += 1
					if is_comment_propaganda(reply.body.lower()):
						print(f"detected propaganda: {reply.body}")

		except prawcore.exceptions.Forbidden:
			continue

	print(f"done in {time() - start_time:.2f} sec ({comments_checked} comments checked)")

def main():

	with ProtectedUsers.load() as protected_users:
		try:
			while True:
				collect_protected_users(bot, protected_users)
				counter_propaganda(bot, protected_users)

		except KeyboardInterrupt:
			print("bye!")

if __name__ == "__main__":
	main()
