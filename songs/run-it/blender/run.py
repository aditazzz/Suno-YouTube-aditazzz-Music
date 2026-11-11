"""Run It: Blender job runner. The render watcher starts it as  Blender -b -P run.py -- <tag> [numbers...]
and it runs blender/jobs/<tag>.py : main(args). Jobs write under songs/run-it/build/bl/ ."""
import sys, os, importlib.util, traceback
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
tag = argv[0] if argv else ''
job = os.path.join(HERE, 'jobs', tag + '.py')
if not os.path.isfile(job):
    print('no such job:', job); sys.exit(2)
sys.path.insert(0, HERE)
spec = importlib.util.spec_from_file_location('job_' + tag, job); mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod); mod.main([float(a) for a in argv[1:]])
except Exception:
    traceback.print_exc(); sys.exit(3)
