import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import re

class DetectionPipeline:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.ml_model = LogisticRegression()
        self.is_trained = False
        self._train_model()

    def _train_model(self):
        dataset_path_forbidden = os.path.join(os.path.dirname(__file__), 'forbidden_question_set_df.csv')
        dataset_path_data = os.path.join(os.path.dirname(__file__), 'data.csv')
        dataset_path_injection = os.path.join(os.path.dirname(__file__), 'prompt_injection_dataset.csv')
        
        if not os.path.exists(dataset_path_forbidden) or not os.path.exists(dataset_path_data) or not os.path.exists(dataset_path_injection):
            print("Warning: Required datasets not found. ML model won't be trained.")
            return

        try:
            # Load original data.csv which contains safe and malicious prompts
            df_data = pd.read_csv(dataset_path_data)
            df_data['target'] = df_data['label'].map({'malicious': 1, 'safe': 0})
            
            # Load a subset of forbidden questions (malicious) to avoid memory issues (file is ~400MB)
            df_forbidden = pd.read_csv(dataset_path_forbidden, nrows=5000)
            df_forbidden['target'] = 1
            df_forbidden['prompt'] = df_forbidden['Prompt']
            
            # Load prompt injection dataset
            df_injection = pd.read_csv(dataset_path_injection)
            df_injection['target'] = df_injection['Label'].str.lower().map({'malicious': 1, 'safe': 0})
            df_injection['prompt'] = df_injection['Prompt']
            
            # Combine all three datasets
            final_df = pd.concat([
                df_data[['prompt', 'target']], 
                df_forbidden[['prompt', 'target']],
                df_injection[['prompt', 'target']]
            ], ignore_index=True)
            final_df = final_df.dropna(subset=['prompt'])
            
            # Rebalance classes conceptually (augment safe data) to prevent the model from blindly predicting 1
            safe_df = final_df[final_df['target'] == 0]
            if not safe_df.empty:
                balanced_safe_df = pd.concat([safe_df] * 100, ignore_index=True)
                final_df = pd.concat([final_df, balanced_safe_df], ignore_index=True)
            
            X = self.vectorizer.fit_transform(final_df['prompt'])
            y = final_df['target']
            
            # Use class_weight to further compensate for the massive malicious class imbalance
            self.ml_model = LogisticRegression(class_weight='balanced')
            self.ml_model.fit(X, y)
            self.is_trained = True
            print("ML model trained successfully.")
        except Exception as e:
            print(f"Error training ML model: {e}")

    def check_signature(self, prompt):
        """Layer 1: Signature-based detection"""
        prompt_lower = prompt.lower()
        signatures = [
            "ignore previous instructions",
            "act as",
            "bypass",
            "reveal system prompt",
            "do anything now",
            "disregard prior context"
        ]
        for sig in signatures:
            if sig in prompt_lower:
                return True, "Signature matched: " + sig
        return False, ""

    def check_heuristic(self, prompt):
        """Layer 2: Heuristic detection"""
        score = 0
        prompt_lower = prompt.lower()
        suspicious_keywords = ["hack", "password", "malware", "keylogger", "exploit", "uncensored"]
        
        # Check suspicious keywords (+2)
        for kw in suspicious_keywords:
            if kw in prompt_lower:
                score += 2

        # Check length (+1)
        if len(prompt) > 150:
            score += 1
            
        # Check encoding patterns (+2)
        # simplistic check for base64 ending in = or hex patterns
        base64_pattern = re.compile(r'^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$')
        hex_pattern = re.compile(r'^(0x)?[0-9a-fA-F]+$')
        
        # split by words and check if any long word looks like encoding
        for word in prompt.split():
            if len(word) > 16:
                if base64_pattern.match(word) or hex_pattern.match(word):
                    score += 2
                    
        # Check excessive symbols (+1)
        symbols = sum(1 for char in prompt if char in "!@#$%^&*()_+{}|:\"<>?~`-=[]\\;',./")
        if symbols > 15:
            score += 1

        if score >= 3: # Threshold
            return True, f"Heuristic score ({score}) exceeded threshold"
            
        return False, ""

    def check_ml(self, prompt):
        """Layer 3: Behaviour-based ML model"""
        if not self.is_trained:
            return False, "ML model not trained"
            
        X_input = self.vectorizer.transform([prompt])
        prediction = self.ml_model.predict(X_input)
        
        if prediction[0] == 1:
            return True, "ML Model detected anomalous behaviour"
        return False, ""

    def analyze_prompt(self, prompt):
        """
        Final Decision Logic:
        If Signature detects -> Block
        Else if Heuristic detects -> Block
        Else if ML detects -> Block
        Else -> Allow
        """
        # Layer 1
        is_sig, sig_reason = self.check_signature(prompt)
        if is_sig:
            return {"status": "Blocked", "layer": "Signature", "reason": sig_reason}

        # Layer 2
        is_heu, heu_reason = self.check_heuristic(prompt)
        if is_heu:
            return {"status": "Blocked", "layer": "Heuristic", "reason": heu_reason}

        # Layer 3
        is_ml, ml_reason = self.check_ml(prompt)
        if is_ml:
            return {"status": "Blocked", "layer": "ML Model", "reason": ml_reason}

        # Safe
        return {"status": "Safe", "layer": "None", "reason": "No malicious intent detected"}

# Singleton instance
pipeline = DetectionPipeline()
