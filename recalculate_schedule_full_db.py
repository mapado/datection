from entities.mongo.activity import Activity
import requests
import frogress
from multiprocessing import Pool
from random import random

# place = Activity.objects(slug = "tulle/les-sept-collines-theatre-de-tulle").first()
# acts = Activity.objects(place = str(place.id))

errors = 0

def activity_refresh(id):
    random_server = int(random()*2)+1 # choose between 1 et 2
    random_server=2 # c3po'+str(random_server)+'.
    ret=requests.put('http://ws.mapado.com:8000/v2/merge/'+str(id)+'/refresh', params={'fields': 'schedule', 'persist': 1}, headers={'Accept-Language': 'fr'})
    if ret.status_code != 200:
        return_status = "{} : {} : {}\n".format(id, ret.status_code, ret.text)
    else:
        return_status = "{} : {}\n".format(id, ret.status_code)
    return return_status

def cb_job_done(result):
    global errors
    global f
    # if not ret.ok:
    #     errors+=1
    f.write(result)
    f.flush()
    progress.next()


batch_size=1000
max_to_recalculate = 2000
last_id = "53196f794d57c22d870c9e02"
#last_id =""
query_args = {
    #'slug' : 'paris/smoking-sofa',
    #'place': '52de7f5a4d57c235cc6e5e37',
    'merged_to_ref': None,
    'activity_type': None
}
if not last_id:
    last_id = Activity.objects(**query_args).order_by('_id').first().id
    # open new log file
    print "Creating a new log file"
    f=open("./datefix.err", "w")
else:
    # append to existing file
    print "Append to existing log file"
    f=open("./datefix.err", "a")

num_to_recalculate = Activity.objects(id__gte=last_id, **query_args).count()

print "{} activities to recalculte".format(num_to_recalculate)

if num_to_recalculate > max_to_recalculate:
    num_to_recalculate=max_to_recalculate

progress = frogress.bar(range(num_to_recalculate))

p = Pool(24)

for step in xrange(0, num_to_recalculate/batch_size):
    acts = Activity.objects(
		id__gte=last_id,
        **query_args
		).order_by('_id').no_cache()[:batch_size]
    #print "get ids"
    #ids = [str(act.id) for act in acts]
    #print "END"

    results = []
    for act in acts:
        r=p.apply_async(activity_refresh, (str(act.id),), callback=cb_job_done)
        results.append(r)
        last_id = act.id
    for r in results:
        r.wait()


f.close()
print errors
print "Last item ID : {}".format(last_id)
