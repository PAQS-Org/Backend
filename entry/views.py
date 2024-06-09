from datetime import datetime

from django.http import HttpResponse


def index(request):
    now = datetime.now()
    html = f'''
    <html>
        <body>
            <h1>Hello from PAQS Team!</h1> 
            <h3>This is a trial</h3>
            <p>The current time is { now }.</p>
            <h3>test by osahene lab</h3>
        </body>
    </html>
    ''' 
    return HttpResponse(html)