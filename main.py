 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/main.py b/main.py
new file mode 100644
index 0000000000000000000000000000000000000000..4697639770ca8aa9d1efe296ff63dfcb024901b5
--- /dev/null
+++ b/main.py
@@ -0,0 +1,12 @@
+"""
+Simple Hello World script.
+"""
+
+
+def main() -> None:
+    """Print a friendly greeting."""
+    print("Hello, world!")
+
+
+if __name__ == "__main__":
+    main()
 
EOF
)
