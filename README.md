# acn-hackathon

ACN Agentic AI Hackathon 2025

# Dependencies

- Python 3.12+
- airefinery-sdk
- flask

Using pip, install the required packages as below:

```
pip install airefinery-sdk
```

```
pip install flask
```

# Setup
To run the demo, a ".env" file at the project root directory is required, 
containing just the below text:
```
API_KEY=<YOUR_API_KEY>
```
where "<YOUR_API_KEY>" should be replaced with your personal API key as provided
by [Accenture AI Refinery](https://airefinery.accenture.com/portal/api-keys).


The data required by "app.py" must be created in advance before running the
application. This includes clothing image data and captions of these images.

To create clothing image data in the subdirectory, "Data/images", along with
a CSV of successfully downloaded data, "uniqlo_downloaded.csv":
```
python catalog_data.py
```

To then caption this image data in a file, "captions.pkl":
```
python refinery.py
```

Without "Data/images", "captions.pkl", and "uniqlo_downloaded.csv" all having
been generated, the main app, "app.py", will not run correctly.


# Run
Run the demo at the project root directory with the command below:
```
flask run
```
then navigate to [the locally running frontend instance](http://localhost:5000/) to try out the demo.

Alternatively, Python can be called directly like so:
```
python app.py
```