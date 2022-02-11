
import praw
import prawcore

from json import dumps, loads
from pathlib import Path
from time import time
from itertools import chain

from bot import bot

with open("information.txt", "r", encoding="utf-8") as f:
	information_text = f.read()

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

	def __len__(self):
		return len(self.users)

class AnsweredComments(ProtectedUsers):

	file_path = Path("answered_comments.txt")

def collect_protected_users(bot, protected_users):

	print("scanning for users to protect...")
	start_time = time()

	if bot.subreddit("antilolitary").user_is_banned:
		print("oh no! bot is banned x-x")
		return

	for obj in chain(bot.subreddit("antilolitary").new(), bot.subreddit("antilolitary").comments()):

		try:
			if obj.author.name not in protected_users:
				print(f" adding {obj.author.name}")
				protected_users.add(obj.author.name)

		except AttributeError:
			pass

	print(f"done in {time() - start_time:.2f} sec")

def is_comment_propaganda(text):

	return all(word in text for word in ("active", "antilolitary", "pedo"))

def check_on_user(redditor, answered_comments):

	comments_checked = 0
	replies_checked = 0
	propaganda_found = 0

	try:
		for comment in redditor.comments.top("day"):

			comments_checked += 1
			comment.reply_sort = "new"

			try:
				comment.refresh()

			except praw.exceptions.ClientException:
				continue
				
			for reply in comment.replies:

				replies_checked += 1

				if is_comment_propaganda(reply.body.lower()) and (reply.id not in answered_comments):

					propaganda_found += 1
					print(f"detected propaganda: {reply.body}")
					print(reply.permalink)
					answered_comments.add(reply.id)
					reply.reply(information_text)

	except (prawcore.exceptions.Forbidden, prawcore.exceptions.NotFound):
		pass

	return comments_checked, replies_checked, propaganda_found

def counter_propaganda(bot, protected_users, answered_comments):

	print("scanning for propaganda...")
	start_time = time()
	comments_checked = 0
	replies_checked = 0
	propaganda_found = 0

	for n, user in enumerate(protected_users, 1):
		
		#print(f"checking user {user} {n}/{len(protected_users)}")
		redditor = praw.models.Redditor(bot, user)
		c, r, p = check_on_user(redditor, answered_comments)
		comments_checked += c
		replies_checked += r
		propaganda_found += p

	print(f"done in {(time() - start_time)/60:.2f} min ({comments_checked} comments checked) ({replies_checked} replies checked) ({propaganda_found} propaganda found)")

def main():

	with ProtectedUsers.load() as protected_users:
		with AnsweredComments.load() as answered_comments:

			try:
				while True:
					collect_protected_users(bot, protected_users)
					counter_propaganda(bot, protected_users, answered_comments)

			except KeyboardInterrupt:
				print("bye!")

if __name__ == "__main__":
	main()
