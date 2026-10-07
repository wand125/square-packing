"""Native radial method: common search/repair and rigorous full-net validation.

Usage matches unified_grid_search --config CONFIG. The configuration must set
radial_mode=native and supply radial_pricing. It can resume native mixed states.
"""
import sys,json
from pathlib import Path
from unified_grid_search import main

if __name__=='__main__':
    if '--config' not in sys.argv:raise SystemExit('required: --config CONFIG')
    config=json.loads(Path(sys.argv[sys.argv.index('--config')+1]).read_text())
    if config.get('radial_mode')!='native' or not config.get('radial_pricing'):raise SystemExit('native method requires radial_mode=native and radial_pricing options')
    main()
