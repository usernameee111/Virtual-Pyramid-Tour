# Virtual Pyramid Tour 🐫

**Explore the Sands of Antiquity**

This project is an interactive, 2D virtual tour of the Giza Plateau built entirely in Python using Pygame. It serves as both an educational historical journey and a practical implementation of low-level computer graphics mathematics. 

Users are guided through dynamic scenes featuring the Pyramids of Khufu, Khafre, and Menkaure, complete with historical facts, a simulated day/night cycle, and an immersive zoom transition into the King's Chamber. Rather than relying on pre-built graphics engines, all core visual elements—from the dynamic shadows to the pyramid structures—are drawn mathematically using fundamental rendering algorithms.

## ✨ Visual & Interactive Features
* **Virtual Guided Tour:** Interactive scenes detailing Khufu, Khafre, and Menkaure with historically accurate facts.
* **Immersive Transitions:** A dynamic zoom-in effect that transports the user from the exterior plateau into the atmospheric interior of the King's Chamber.
* **Dynamic Environment:** Features a mathematical sun trajectory, procedural floating dust particles, and dynamic shadow rendering based on light position.

## ⚙️ Technical Implementations (Under the Hood)
* **DDA & Bresenham's Line Algorithms:** Custom-built functions for precise pixel-by-pixel line drawing.
* **Midpoint Circle Algorithm:** Used for rendering smooth, filled celestial objects and character elements.
* **Scanline Triangle Fill:** Custom polygon filling logic used to architect the pyramid structures layer by layer.
