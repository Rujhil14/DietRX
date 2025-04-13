from flask import Flask, render_template, redirect

app = Flask(__name__)

# Route for the homepage (index page)
@app.route('/')
def index():
    return render_template('common/index.html')

# Route for "How to Use" page
@app.route('/how_to_use')
def how_to_use():
    return render_template('common/how_to_use.html')

@app.route('/faq')
def faq():
    # Fetch or generate the 'stats' data (this is just an example)
    stats = {
        'fd_foods': 100,  # Example data
        'fcats': 5,
        'chems': 150,
        'fc_foods': 50,
    }

    # Render the FAQ page with the 'stats' variable
    return render_template('common/faq.html', stats=stats)

# Route for "Contact Us" page
@app.route('/contact_us')
def contact_us():
    return render_template('common/contact_us.html')

# Route for "Search" page
@app.route('/search')
def search():
    return render_template('search/search.html')

# Route for Analytics (external link, no need for template)
@app.route('/analytics')
def analytics():
    return redirect("http://cosylab.iiitd.edu.in/dietrx/analytics/")

if __name__ == '__main__':
    # Run the app on localhost (default port 5000)
    app.run(debug=True)
