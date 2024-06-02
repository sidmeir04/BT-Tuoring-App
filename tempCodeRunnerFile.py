    for _ in range(1,10):
            newThing = Periods()
            db.session.add(newThing)
            db.session.commit()