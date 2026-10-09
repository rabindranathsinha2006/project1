from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .assistant_engine import generate_assistant_response

def assistant_page_view(request):
    return render(request, 'assistant/assistant.html')

@csrf_exempt
def assistant_chat_api(request):
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                query = data.get('query', '').strip()
            else:
                query = request.POST.get('query', '').strip()
        except Exception:
            query = ''

        if not query:
            return JsonResponse({
                'success': False,
                'message': "Please enter what you are looking for."
            })

        response_data = generate_assistant_response(query)
        return JsonResponse({
            'success': True,
            'query': query,
            **response_data
        })

    return JsonResponse({'success': False, 'message': 'Only POST method is allowed.'})
