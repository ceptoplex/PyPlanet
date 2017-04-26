from pyplanet.apps.config import AppConfig
from pyplanet.apps.contrib.karma.views import KarmaListView
from pyplanet.contrib.command import Command

from pyplanet.apps.core.maniaplanet import callbacks as mp_signals

from .models import Karma


class KarmaConfig(AppConfig):
	name = 'pyplanet.apps.contrib.karma'
	game_dependencies = []
	app_dependencies = ['core.maniaplanet']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.current_votes = []
		self.current_karma = 0
		self.current_positive_votes = 0
		self.current_negative_votes = 0

	async def on_start(self):
		# Register commands.
		await self.instance.command_manager.register(Command(command='whokarma', target=self.show_map_list))

		# Register signals.
		self.instance.signal_manager.listen(mp_signals.map.map_begin, self.map_begin)
		self.instance.signal_manager.listen(mp_signals.player.player_chat, self.player_chat)

		# Load initial data.
		await self.get_votes_list(self.instance.map_manager.current_map)
		await self.calculate_karma()
		await self.chat_current_karma()

	async def show_map_list(self, player, map=None, **kwargs):
		"""
		Show map list to player for current map or map provided.. Provide player instance.
		
		:param player: Player instance. 
		:param map: Map instance or current map.
		:param kwargs: ...
		:type player: pyplanet.apps.core.maniaplanet.models.Player
		:return: View instance.
		"""
		view = KarmaListView(self, map or self.instance.map_manager.current_map)
		await view.display(player=player.login)
		return view

	async def map_begin(self, map):
		await self.get_votes_list(map)
		await self.calculate_karma()
		await self.chat_current_karma()

	async def player_chat(self, player, text, cmd):
		if not cmd:
			if text == '++' or text == '--':
				score = (1 if text == '++' else -1)
				player_votes = [x for x in self.current_votes if x.player_id == player.get_id()]
				if len(player_votes) > 0:
					player_vote = player_votes[0]
					if player_vote.score != score:
						player_vote.score = score
						await player_vote.save()

						message = '$z$s$fff» $ff0Successfully changed your karma vote to $fff{}$ff0!'.format(text)
						await self.instance.gbx.execute('ChatSendServerMessageToLogin', message, player.login)
				else:
					new_vote = Karma(map=self.instance.map_manager.current_map,player=player,score=score)
					await new_vote.save()

					self.current_votes.append(new_vote)
					await self.calculate_karma()

					message = '$z$s$fff» $ff0Successfully voted $fff{}$ff0!'.format(text)
					await self.instance.gbx.execute('ChatSendServerMessageToLogin', message, player.login)

	async def get_votes_list(self, map):
		vote_list = await Karma.objects.execute(Karma.select().where(Karma.map_id == map.get_id()))
		self.current_votes = list(vote_list)

	async def calculate_karma(self):
		self.current_positive_votes = [x for x in self.current_votes if x.score == 1]
		self.current_negative_votes = [x for x in self.current_votes if x.score == -1]
		self.current_karma = (len(self.current_positive_votes) - len(self.current_negative_votes))

	async def chat_current_karma(self):
		num_current_votes = len(self.current_votes)
		message = '$z$s$fff»» $ff0Current map karma: $fff{}$ff0 [$fff{}$ff0 votes, ++: $fff{}$ff0 ($fff{}%$ff0), --: $fff{}$ff0 ($fff{}%$ff0)'.format(
			self.current_karma, num_current_votes,
			len(self.current_positive_votes),
			round((len(self.current_positive_votes) / num_current_votes) * 100, 2) if num_current_votes > 0 else 0,
			len(self.current_negative_votes),
			round((len(self.current_negative_votes) / num_current_votes) * 100, 2) if num_current_votes > 0 else 0,
		)
		await self.instance.gbx.execute('ChatSendServerMessage', message)