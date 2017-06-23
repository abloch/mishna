#!/usr/bin/env python
import os
import pickle
import requests

URL_BASE = "http://www.sefaria.org/api/texts"
mishnafile = os.path.join(os.path.dirname(__file__), 'current.pkl')

all_masehet = None
def flatten(lst):
	return [item for sublist in lst for item in sublist]

def get_all_titles(category=None):
	resp=requests.get("http://www.sefaria.org/api/index").json()
	if category:
		return [book for book in resp if category in book['category']]
	return resp

def get_all_masehet():
	global all_masehet
	if all_masehet is None:
		all_masehet = [b['title'] for b in flatten(flatten(get_all_contents(get_all_titles("Mishna")))) if "title" in b]
	return all_masehet

def get_all_contents(books):
	return [get_all_contents(book['contents']) if "contents" in book else book for book in books]

def get_next_masehet(masehet=None):
	if not masehet:
		return get_all_masehet()[0]
	return get_all_masehet()[get_all_masehet().index(masehet) + 1]

class Mishna:
	def __init__(self, masehet, chapter, mishna, _chapter=None):
		self.masehet = masehet
		self.chapter = chapter
		self.mishna = mishna
		self._chapter = _chapter

	def get_chapter(self):
		if self._chapter: return self._chapter
		url = "{}/{}.{}".format(URL_BASE, self.masehet, self.chapter)
		self._chapter = requests.get(url).json()
		return self._chapter

	def get_title(self):
		return "{} {}".format(self.get_chapter()['heSectionRef'], self.mishna+1)

	def get_text(self):
		return self.get_chapter()['he'][self.mishna].strip()

	def is_last_in_chapter(self):
		return self.mishna + 1 >= len(self.get_chapter()['he'])

	def get_next(self):
		if not self.is_last_in_chapter():
			return Mishna(self.masehet, self.chapter, self.mishna+1, self._chapter)
		if self.get_chapter()['next']:  # there's another chapter in the masehet
			return Mishna(self.masehet, self.chapter+1, 0, None)
		return Mishna(get_next_masehet(self.masehet), 1, 0)

	def get_commentaries(self):
		return "_ברטנורא:_ http://www.sefaria.org/Bartenura_on_{}_{}?lang=he\n".format(self.masehet.replace(" ", "_"), self.chapter) + \
			"_תוספות יום טוב:_ " + \
			"http://www.sefaria.org/Ikar_Tosafot_Yom_Tov_on_{}_{}?lang=he\n".format(self.masehet.replace(" ", "_"), self.chapter) + \
			'_רמב"ם:_ ' + \
			"http://www.sefaria.org/Rambam_on_{}_{}?lang=he\n".format(self.masehet.replace(" ", "_"), self.chapter)

	def __str__(self):
		return self.get_title() + "\n\n" + self.get_text() + "\n\n" + self.get_commentaries() + "\n\n"

	@classmethod
	def load_current(cls):
		if os.path.exists(mishnafile):
			with open(mishnafile, "rb") as f:
				return pickle.load(f)
		else:
			return Mishna("Mishnah Bava Metzia", 8, 2)


	def save_as_current(self):
		with open(mishnafile, "wb") as f:
			pickle.dump(self, f)

if __name__ == "__main__":
	current = Mishna.load_current()
	next = current.get_next()
	print(next)
	next.save_as_current()

