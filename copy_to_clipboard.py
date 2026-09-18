import subprocess

desc = """Welcome to Daily Dose of Science! 🌌🔬🚀

Your daily destination for mind-bending science facts, cosmic mysteries, quantum paradoxes, and crazy engineering wonders explained in seconds! From the depths of black holes to the edge of the observable universe, we explore the wildest questions in physics, space, and nature.

✨ What We Explore Daily:
🌌 Space, Black Holes & Cosmic Wonders
⚛️ Quantum Mechanics, Time Dilation & Einstein’s Relativity
🧠 Mind-blowing "What If..." & "Did You Know..." Science Scenarios
✈️ Military Aviation, Stealth Tech & Engineering Marvels
🌿 Nature’s Bizarre Phenomena & Biology Paradoxes

Whether you are a science nerd, a curious student, or someone who loves to be amazed by reality, subscribe to fuel your daily curiosity! 💡

🔔 New mind-blowing shorts every single day!

----------------------------------------
⚖️ Fair Use Notice:
This channel shares educational content under the Fair Use doctrine (Section 107 of the US Copyright Act). If you are a copyright owner and have any concerns, please contact us directly — we will gladly cooperate.

#Science #Physics #SpaceFacts #DailyDoseOfScience #Scienceverse #DidYouKnow #Shorts #Cosmology #Engineering"""

# Set to Windows clipboard via powershell
process = subprocess.Popen(['powershell', '-Command', 'Set-Clipboard -Value $input'], stdin=subprocess.PIPE, text=True, encoding='utf-8')
process.communicate(input=desc)
print("SEO Description successfully copied to Windows clipboard!")
