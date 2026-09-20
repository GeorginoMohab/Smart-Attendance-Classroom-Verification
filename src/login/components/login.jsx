import { useState } from "react";
import api from "../../api/axios";
import "./login.css";
import LogoBUA from "../../Logo_BUA.jpeg";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [message, setMessage] = useState("");

  async function handleLogin(e) {
    // Prevent the form from refreshing the page
    e.preventDefault();

    // Clear old messages
    setEmailError("");
    setPasswordError("");
    setMessage("");

    let valid = true;

    // Email validation
    if (email.trim() === "") {
      setEmailError("Email is required");
      valid = false;
    }

    // Password validation
    if (password.trim() === "") {
      setPasswordError("Password is required");
      valid = false;
    }

    // Stop if validation failed
    if (!valid) {
      return;
    }

    try {
      const response = await api.post("/auth/login", {
        email: email,
        password: password,
      });

      console.log("Token:", response.data.token);
      console.log("Role:", response.data.role);

      setMessage("Login successful");
    } catch (error) {
  console.log("ERROR:", error);
  console.log("RESPONSE:", error.response);
  console.log("DATA:", error.response?.data);

  setMessage(
    error.response?.data?.error ||
    error.message ||
    "Login failed"
  );
}
  }

  return (
  <div className="login-container">
    <img src={LogoBUA} alt="BUA Logo" />

    <form onSubmit={handleLogin}>
      <div className="form-group">
        <label htmlFor="exampleInputEmail1">
          Email address
        </label>

        <input
          type="email"
          className="form-control"
          id="exampleInputEmail1"
          aria-describedby="emailHelp"
          placeholder="Enter email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        {emailError && (
          <p>{emailError}</p>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="exampleInputPassword1">
          Password
        </label>

        <input
          type="password"
          className="form-control"
          id="exampleInputPassword1"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {passwordError && (
          <p>{passwordError}</p>
        )}
      </div>

      <div className="form-check">
        <input
          type="checkbox"
          className="form-check-input"
          id="exampleCheck1"
        />

        <label
          className="form-check-label"
          htmlFor="exampleCheck1"
        >
          Check me out
        </label>
      </div>

      <button
        type="submit"
        className="btn-btn-primary"
      >
        Submit
      </button>

      {message && (
        <p>{message}</p>
      )}
    </form>
  </div>
);
}

export default Login;