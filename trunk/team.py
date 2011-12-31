# Iron Puzzler team page handler

import logging

from google.appengine.dist import use_library;  use_library('django', '1.2')
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import model
import login
from puzzle import NormalizeScore


class TeamPage(webapp.RequestHandler):
  def get(self):
    game = model.GetGame()
    team = login.GetTeamOrRedirect(game, self.request, self.response)
    if not team: return

    props = {
      "error": self.request.get_all("error"),
      "game": model.GetProperties(game),
      "team": model.GetProperties(team),
      "team_puzzles": [],
      "other_puzzles": [],
      "errata_puzzles": [],
    }

    puzzle_props = {}
    for n, puzzle in enumerate(model.Puzzle.get(game.puzzle_order)):
      pp = puzzle_props[puzzle.key()] = model.GetProperties(puzzle)
      pp["number"] = n + 1
      pp["guess_count"] = 0
      pp["answers"] = set(puzzle.answers)
      pp["solve_teams"] = set()
      if pp.get("errata"):
        props["errata_puzzles"].append(pp)
      if puzzle.parent_key() == team.key():
        props["team_puzzles"].append(pp)
      else:
        props["other_puzzles"].append(pp)

    feedback_keys = [
        db.Key.from_path("Feedback", str(team.key()), parent=pk)
        for pk in game.puzzle_order if pk.parent() != team.key()]
    for key, feedback in zip(feedback_keys, model.Feedback.get(feedback_keys)):
      pp = puzzle_props.get(key.parent())
      if pp: pp["feedback"] = model.GetProperties(
          feedback or model.Feedback(key=key))

    for guess in model.Guess.all().ancestor(game):
      pp = puzzle_props.get(guess.parent_key())
      if not pp: continue

      if guess.answer in pp["answers"]:
        pp["solve_teams"].add(guess.team.key())

      if guess.team.key() == team.key():
        if guess.answer in pp["answers"]: pp["solve_time"] = guess.timestamp
        pp["guess_count"] += 1

    self.response.out.write(template.render("team.dj.html", props))


  def post(self):
    game = model.GetGame()
    team = login.GetTeamOrRedirect(game, self.request, self.response)
    if not team: return

    if game.voting_enabled:
      sr = range(len(model.Feedback().scores))
      for n, pk in enumerate(game.puzzle_order):
        score = [self.request.get("score.%d.%d" % (n + 1, s)) for s in sr]
        orig = [self.request.get("score.%d.%d.orig" % (n + 1, s)) for s in sr]
        if score != orig:
          feedback = model.Feedback.get_or_insert(str(team.key()), parent=pk)
          for s in sr: feedback.scores[s] = NormalizeScore(score[s])
          feedback.put()

    self.redirect("/team?t=%d" % team.key().id())
    team.name = self.request.get("name") or team.name
    team.email = self.request.get("email")

    set_pw = self.request.get("set_password")
    confirm_pw = self.request.get("confirm_password")
    if set_pw or confirm_pw:
      if set_pw != confirm_pw:
        self.response.headers["location"] += "&error=set_password"
      else:
        team.password = set_pw

    team.put()


app = webapp.WSGIApplication([("/team", TeamPage)], debug=True)
if __name__ == "__main__": run_wsgi_app(app)