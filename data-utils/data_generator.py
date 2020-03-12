from faker import Faker

fake = Faker(["it_IT", "en_UK", "es_MX"])

users = [
    dict(
        name=fake.name(),
        address=fake.address(),
        job=fake.job(),
        dateOfBirth=fake.date_of_birth(
            tzinfo=None, minimum_age=0, maximum_age=115
        ).isoformat(),
    )
    for _ in range(100)
]

print(users)
