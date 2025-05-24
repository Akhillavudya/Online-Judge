# AlgoU Online Compiler

An end-to-end web application that lets you write, compile, and execute code directly in the browser.

The project is split into two independently runnable parts:

1. **backend** – A lightweight Express server that receives source-code, stores it temporarily, compiles it with `g++`, then streams the program output back to the client.
2. **frontend** – A React + Vite single-page application that provides a minimal online IDE and communicates with the backend via REST.

---

## ✨ Features

• Live, in-browser code editing powered by `react-simple-code-editor` and Prism syntax highlighting.

• One-click **Run** button – code is POSTed to the server, compiled, and the result appears instantly below the editor.

• Modular execution pipeline – only C++ is wired-up at the moment, but adding more languages is as simple as creating an `execute<LANG>.js` helper and a small switch-case.

---

## 🛠 Installation

> These commands assume you have **Node.js ≥ 18** and **npm** installed.

1. Clone the repo & move into the project folder:

```bash
$ git clone https://github.com/your-username/AlgoU-Online-Compiler.git
$ cd AlgoU-Online-Compiler
```

2. Install dependencies for both workspaces:

```bash
# Back-end
$ cd backend && npm install

# Front-end
$ cd ../frontend && npm install
```

3. (Optional) copy the environment variable template and tweak if necessary:

```bash
$ cp backend/.env.example backend/.env
```

---

## ▶️ Running the project

Open two terminals – one for each side of the stack:

```bash
# Terminal 1 – API
$ cd backend
$ npm run dev        # Auto-restarts with nodemon

# Terminal 2 – React SPA
$ cd frontend
$ npm run dev        # Starts Vite on http://localhost:5173
```

The React app expects the API to be reachable at `http://localhost:5000`. If you change the port, make sure to update the Axios URL inside `frontend/src/App.jsx`.

---

## 📦 Example usage

1. Type or paste some C++ code into the editor.
2. Click **Run**.
3. The program output appears in the grey box underneath.

![Screenshot](frontend/Snapshot.png)

---

## ⚙️ Dependencies

### Back-end

- express
- cors
- uuid
- nodemon (development)

### Front-end

- react + react-dom
- vite
- react-simple-code-editor
- prismjs
- tailwindcss + postcss + autoprefixer

A full, pinned list can be found in each workspace's `package.json` file.

---

## 🤝 Contributing

Pull-requests are welcome! Please open an issue first so we can discuss what you plan to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m "feat: add amazing feature"`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT © 2024 Your Name
