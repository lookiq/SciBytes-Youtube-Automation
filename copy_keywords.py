import subprocess

keywords = "SciBytes, Scienceverse, science facts, space facts, did you know, what happens if you, physics, astronomy, black hole, quantum physics, solar system, NASA, James Webb, how things work, engineering, universe, cosmos, science shorts, physics shorts, viral science facts, interesting facts, mysteries of universe, time dilation, general relativity, documentary clips, Kurzgesagt, Veritasium, AstroKobi, science documentary"

process = subprocess.Popen(['powershell', '-Command', 'Set-Clipboard -Value $input'], stdin=subprocess.PIPE, text=True, encoding='utf-8')
process.communicate(input=keywords)
print("Keywords copied to clipboard!")
