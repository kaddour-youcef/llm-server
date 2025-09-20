from locust import HttpUser, task, between
import random

# Example prompts of different sizes
SHORT_PROMPT = "Hello, how are you?"
LONG_PROMPT = " ".join(["This is a long stress test sentence."] * 200)  # ~200 sentences

class ChatUser(HttpUser):
    wait_time = between(1, 3)  # users wait between 1-3s between actions

    @task(5)  # Weighted higher → 5x more likely
    def normal_chat(self):
        """Simulates a normal chat message."""
        self.client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": SHORT_PROMPT}],
            },
            headers={"Authorization": "Bearer test-key"}  # replace with your API key
        )

    @task(2)
    def bursty_chat(self):
        """Sends a burst of requests to test Redis rate limits."""
        for _ in range(random.randint(3, 7)):  # short bursts
            self.client.post(
                "/v1/chat/completions",
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": SHORT_PROMPT}],
                },
                headers={"Authorization": "Bearer test-key"}
            )

    @task(1)
    def long_prompt_chat(self):
        """Send a very long prompt to stress token counting."""
        self.client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": LONG_PROMPT}],
            },
            headers={"Authorization": "Bearer test-key"}
        )
