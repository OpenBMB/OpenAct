import os
import pickle

from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)
cache_file = "cache.pkl"
# This file intends to show the cached image list in web browser
# Make sure you have cache.pkl in the repo's root dir

# Function to save cache to file


def save_cache(cache):
    with open(cache_file, "wb") as f:
        pickle.dump(cache, f)


# Function to load cache from file


def load_cache():
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    return {}


# Function to update a specific cache item
cache = load_cache()


@app.route("/update/<key>", methods=["GET", "POST"])
@app.route("/update/<key>", methods=["GET", "POST"])
def update_cache_item(key):
    cache = load_cache()
    if request.method == "POST":
        if "delete_key" in request.form:
            # delete
            sub_key = request.form["delete_key"]
            if sub_key in cache[key]:
                del cache[key][sub_key]
                save_cache(cache)
                return redirect(url_for("update_cache_item", key=key))
        else:
            # update
            if key in cache:
                updated_item = {
                    k: request.form.get(k, v) for k, v in cache[key].items()
                }
                cache[key] = updated_item
                save_cache(cache)
        return redirect(url_for("home"))

    return render_template_string(
        """
        <!doctype html>
        <html>
        <head>
            <title>Update Cache Item</title>
            <style>
                .key-value-pair {
                    margin-bottom: 10px;
                }
                textarea {
                    width: 400px;  
                    height: 100px;
                    padding: 10px;
                    box-sizing: border-box;
                    resize: vertical;
                }
                .delete-button {
                    margin-left: 10px;
                }
            </style>
        </head>
        <body>
            <h2>Update Cache Item: {{ key }}</h2>
            <form method="post">
                {% for sub_key, sub_value in cache[key].items() %}
                    <div class="key-value-pair">
                        {{ sub_key }}: <textarea name="{{ sub_key }}">{{ sub_value }}</textarea>
                        <button type="submit" class="delete-button" name="delete_key" value="{{ sub_key }}">Delete</button>
                    </div>
                {% endfor %}
                <input type="submit" value="Update">
            </form>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """,
        key=key,
        cache=cache,
    )


# Function to delete a specific cache item


@app.route("/delete/<key>", methods=["GET"])
def delete_cache_item(key):
    cache = load_cache()
    if key in cache:
        del cache[key]
        save_cache(cache)
    return redirect(url_for("home"))


# Function to add a new cache item


@app.route("/add", methods=["GET", "POST"])
def add_cache_item():
    if request.method == "POST":
        key = request.form["key"]
        # get key-value pair
        value = {}
        for form_key in request.form:
            if form_key.startswith("value_key_"):
                value_number = form_key.split("_")[-1]
                value_key = request.form[form_key]
                value_value = request.form.get(f"value_value_{value_number}", "")
                value[value_key] = value_value

        cache = load_cache()
        cache[key] = value
        save_cache(cache)
        return redirect(url_for("home"))
    return render_template_string(
        """
    <!doctype html>
    <html>
    <head>
        <title>Add Cache Item</title>
        <style>
            textarea {
                width: 1000px;
                height: 100px;
                padding: 10px;
                margin: 5px 0;
                box-sizing: border-box;
                resize: vertical;
            }
        </style>
    </head>
    <body>
        <h2>Add New Cache Item</h2>
        <form method="post">
            Key: <textarea name="key"></textarea><br>
            <div id="key-value-pairs">
                Value Key: <textarea name="value_key_1"></textarea><br>
                Value: <textarea name="value_value_1"></textarea><br>
            </div>
            <button type="button" onclick="addKeyValuePair()">Add Another Key-Value Pair</button><br>
            <input type="submit" value="Save">
        </form>
        <a href="/">Back to Home</a>
        <script>
            let pairCount = 1;
            function addKeyValuePair() {
                pairCount++;
                let div = document.createElement('div');
                div.innerHTML = 'Value Key: <textarea name="value_key_' + pairCount + '"></textarea><br>' +
                                'Value: <textarea name="value_value_' + pairCount + '"></textarea><br>';
                document.getElementById('key-value-pairs').appendChild(div);
            }
        </script>
    </body>
    </html>
    """
    )


@app.route("/delete-key-value/<key>", methods=["GET", "POST"])
def delete_key_value(key):
    cache = load_cache()
    if request.method == "POST":
        sub_key = request.form.get("sub_key")
        if key in cache and sub_key in cache[key]:
            del cache[key][sub_key]
            save_cache(cache)
        return redirect(url_for("home"))

    return render_template_string(
        """
        <!doctype html>
        <html>
        <head>
            <title>Delete Key-Value Pair</title>
        </head>
        <body>
            <h2>Delete Key-Value Pair from '{{ key }}'</h2>
            <form method="post">
                Select Key to Delete: <select name="sub_key">
                    {% for sub_key in cache[key].keys() %}
                        <option value="{{ sub_key }}">{{ sub_key }}</option>
                    {% endfor %}
                </select>
                <input type="submit" value="Delete">
            </form>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """,
        key=key,
        cache=cache,
    )


# Home page


@app.route("/", methods=["GET", "POST"])
def home():
    cache = load_cache()
    return render_template_string(
        """
    <!doctype html>
    <html>
    <head>
        <title>Cache Manager</title>
        <style>
            textarea {
                width: 1000px;
                height: 100px;
                padding: 10px;
                margin: 5px 0;
                box-sizing: border-box;
                resize: vertical;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            td, th {
                border: 1px solid black;
                padding: 5px;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <h2>Cache Contents</h2>
        <table>
        {% for key, value in cache.items() %}
            <tr>
                <td>{{ key }}</td>
                <td>
                    <table>
                    {% for sub_key, sub_value in value.items() %}
                        <tr><td>{{ sub_key }}</td><td>{{ sub_value }}</td></tr>
                    {% endfor %}
                    </table>
                </td>
                <td><a href="/update/{{ key }}">Edit</a></td>
                <td><a href="/delete/{{ key }}">Delete</a></td>
            </tr>
        {% endfor %}
        </table>
        <h2>Add Cache Item</h2>
        <a href="/add">Add New Cache Item</a>
    </body>
    </html>
    """,
        cache=cache,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5002)
