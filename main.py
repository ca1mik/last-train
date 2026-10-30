from lasttrain.app import main

if __name__ == '__main__':
    try:
        main()
    except Exception:
        import os
        import traceback
        from pathlib import Path
        log=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'LastTrain'/'crash.log'
        try:
            log.parent.mkdir(parents=True,exist_ok=True)
            log.write_text(traceback.format_exc(),encoding='utf-8')
        except OSError:
            pass
        raise
