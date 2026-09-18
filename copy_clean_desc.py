import subprocess

desc_clean = """Welcome to Daily Dose of Science!

Your daily destination for mind-bending science facts, cosmic mysteries, quantum paradoxes, and engineering wonders explained in seconds. From the depths of black holes to the edge of the observable universe, we explore the wildest questions in physics, space, and nature.

What We Explore Daily:
- Space, Black Holes and Cosmic Wonders
- Quantum Mechanics, Time Dilation and Einstein's Relativity
- Mind-blowing 'What If...' and 'Did You Know...' Science Scenarios
- Military Aviation, Stealth Technology and Engineering Marvels
- Nature's Bizarre Phenomena and Biology Paradoxes

Whether you are a science enthusiast, a student, or simply curious about how reality works, subscribe to fuel your daily curiosity!

New educational shorts every single day.

----------------------------------------
Fair Use Notice:
This channel shares educational content under the Fair Use doctrine (Section 107 of the US Copyright Act). If you are a copyright owner and have any concerns, please contact us directly - we will gladly cooperate.

#Science #Physics #SpaceFacts #DailyDoseOfScience #Scienceverse #DidYouKnow #Shorts #Cosmology #Engineering"""

# Set to Windows clipboard via powershell
process = subprocess.Popen(['powershell', '-Command', 'Set-Clipboard -Value $input'], stdin=subprocess.PIPE, text=True, encoding='utf-8')
process.communicate(input=desc_clean)
print("Clean description (no emojis) copied to clipboard!")
