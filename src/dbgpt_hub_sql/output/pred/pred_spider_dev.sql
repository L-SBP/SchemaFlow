SELECT count(*) FROM singer
SELECT count(*) FROM singer
SELECT name ,  country ,  age FROM singer ORDER BY age DESC
SELECT name ,  country ,  age FROM singer ORDER BY age DESC
SELECT avg(age) ,  min(age) ,  max(age) FROM singer WHERE Country  =  'France'
SELECT avg(age) ,  min(age) ,  max(age) FROM singer WHERE country  =  'French'
SELECT song_name ,  song_release_year FROM singer ORDER BY age LIMIT 1
SELECT song_name ,  song_release_year FROM singer ORDER BY age LIMIT 1
SELECT DISTINCT country FROM singer WHERE age  >  20
SELECT DISTINCT country FROM singer WHERE age  >  20
SELECT country ,  count(*) FROM singer GROUP BY country
SELECT country ,  count(*) FROM singer GROUP BY country
SELECT song_name FROM singer WHERE age  >  (SELECT average FROM stadium)
SELECT Song_Name FROM singer WHERE Age  >  (SELECT Average FROM stadium)
SELECT LOCATION ,  name FROM stadium WHERE capacity BETWEEN 5000 AND 10000
SELECT location ,  name FROM stadium WHERE capacity BETWEEN 5000 AND 10000
SELECT max(capacity) ,  avg(*) FROM stadium
SELECT average ,  highest FROM stadium
SELECT name ,  capacity FROM stadium ORDER BY average DESC LIMIT 1
SELECT name ,  capacity FROM stadium ORDER BY average DESC LIMIT 1
SELECT count(*) FROM concert WHERE YEAR  =  2014 OR YEAR  =  2015
SELECT count(*) FROM concert WHERE YEAR  =  2014 OR YEAR  =  2015
SELECT T2.Name ,  COUNT(*) FROM concert AS T1 JOIN stadium AS T2 ON T1.Stadium_ID  =  T2.Stadium_ID GROUP BY T1.Stadium_ID
SELECT T2.Theme ,  count(*) FROM concert AS T1 JOIN stadium AS T2 ON T1.Stadium_ID  =  T2.Stadium_ID GROUP BY T1.Stadium_ID
SELECT T2.name ,  T1.capacity FROM concert AS T1 JOIN stadium AS T2 ON T1.Stadium_ID  =  T2.Stadium_ID WHERE T1.year  >=  2014 GROUP BY T1.Stadium_ID ORDER BY count(*) DESC LIMIT 1
SELECT T2.name ,  T2.capacity FROM concert AS T1 JOIN stadium AS T2 ON T1.Stadium_ID  =  T2.Stadium_ID WHERE T1.year  >  2013 GROUP BY T1.Stadium_ID ORDER BY count(*) DESC LIMIT 1
SELECT YEAR FROM concert GROUP BY YEAR ORDER BY count(*) DESC LIMIT 1
SELECT YEAR FROM concert GROUP BY YEAR ORDER BY count(*) DESC LIMIT 1
SELECT name FROM stadium WHERE stadium_id NOT IN (SELECT stadium_id FROM concert)
SELECT name FROM stadium WHERE stadium_id NOT IN (SELECT stadium_id FROM concert)
SELECT country FROM singer WHERE age  >  40 INTERSECT SELECT country FROM singer WHERE age  <  30
SELECT name FROM stadium EXCEPT SELECT T2.name FROM concert AS T1 JOIN stadium AS T2 ON T1.Stadium_ID  =  T2.Stadium_ID WHERE T1.year  =  2014
SELECT name FROM stadium EXCEPT SELECT T2.name FROM concert AS T1 JOIN stadium AS T2 ON T1.Stadium_ID  =  T2.Stadium_ID WHERE T1.year  =  2014
SELECT T2.concert_name ,  COUNT(*) FROM singer_in_concert AS T1 JOIN concert AS T2 ON T1.concert_id  =  T2.concert_id GROUP BY T1.concert_id
SELECT T2.concert_name ,  T1.Theme ,  count(*) FROM concert AS T1 JOIN singer_in_concert AS T2 ON T1.concert_ID  =  T2.concert_ID GROUP BY T1.concert_ID
SELECT T2.name ,  count(*) FROM singer_in_concert AS T1 JOIN singer AS T2 ON T1.Singer_ID  =  T2.Singer_ID GROUP BY T2.name
SELECT T2.name ,  count(*) FROM singer_in_concert AS T1 JOIN singer AS T2 ON T1.Singer_ID  =  T2.Singer_ID GROUP BY T2.name
SELECT T2.name FROM singer_in_concert AS T1 JOIN singer AS T2 ON T1.Singer_ID  =  T2.Singer_ID JOIN concert AS T3 ON T3.concert_ID  =  T1.concert_ID WHERE T3.year  =  2014
SELECT T2.name FROM singer_in_concert AS T1 JOIN singer AS T2 ON T1.singer_id  =  T2.singer_id JOIN concert AS T3 ON T3.concert_id  =  T1.concert_id WHERE T3.year  =  2014
SELECT name ,  country FROM singer WHERE Song_Name LIKE '%Hey%'
SELECT name ,  country FROM singer WHERE song_name LIKE '%Hey%'
SELECT T2.name ,  T2.location FROM concert AS T1 JOIN stadium AS T2 ON T1.Stadium_ID  =  T2.Stadium_ID WHERE T1.year  =  2014 INTERSECT SELECT T2.name ,  T2.location FROM concert AS T1 JOIN stadium AS T2 ON T1.Stadium_ID  =  T2.Stadium_ID WHERE T1.year  =  2015
SELECT T2.name ,  T2.location FROM concert AS T1 JOIN stadium AS T2 ON T1.Stadium_ID  =  T2.Stadium_ID WHERE T1.year  =  2014 INTERSECT SELECT T2.name ,  T2.location FROM concert AS T1 JOIN stadium AS T2 ON T1.Stadium_ID  =  T2.Stadium_ID WHERE T1.year  =  2015
SELECT count(*) FROM concert AS T1 JOIN stadium AS T2 ON T1.Stadium_ID  =  T2.Stadium_ID WHERE T2.Name  =  (SELECT Name FROM stadium ORDER BY highest DESC LIMIT 1)
SELECT count(*) FROM concert AS T1 JOIN stadium AS T2 ON T1.Stadium_ID  =  T2.Stadium_ID WHERE T2.capacity  =  (SELECT max(capacity) FROM stadium)
SELECT count(*) FROM pets WHERE weight  >  10
SELECT count(*) FROM pets WHERE weight  >  10
SELECT weight FROM pets WHERE pet_age  =  (SELECT min(pet_age) FROM pets WHERE pettype  =  "Dog")
SELECT weight FROM pets WHERE pet_age  =  (SELECT min(pet_age) FROM pets WHERE pettype  =  'Dog')
SELECT max(weight) ,  pettype FROM pets GROUP BY pettype
SELECT max(weight) ,  PetType FROM Pets GROUP BY PetType
SELECT count(*) FROM has_pet AS T1 JOIN student AS T2 ON T1.stuid  =  T2.stuid WHERE T2.age  >  20
SELECT count(*) FROM student AS T1 JOIN has_pet AS T2 ON T1.stuid  =  T2.stuid WHERE T1.age  >  20
SELECT count(*) FROM pets AS T1 JOIN has_pet AS T2 ON T1.petid  =  T2.petid JOIN student AS T3 ON T3.stuid  =  T2.stuid WHERE T1.pettype  =  'Dog' AND T3.sex  =  'F'
SELECT count(*) FROM student AS T1 JOIN has_pet AS T2 ON T1.stuid  =  T2.stuid JOIN pets AS T3 ON T2.petid  =  T3.petid WHERE T3.pettype  =  'Dog' AND T1.sex  =  'F'
SELECT count(DISTINCT pettype) FROM pets
SELECT count(DISTINCT pettype) FROM pets
SELECT DISTINCT T1.fname FROM student AS T1 JOIN has_pet AS T2 ON T1.stuid  =  T2.stuid JOIN pets AS T3 ON T2.petid  =  T3.petid WHERE T3.pettype  =  'Cat' OR T3.pettype  =  'Dog'
SELECT DISTINCT T1.fname FROM student AS T1 JOIN has_pet AS T2 ON T1.stuid  =  T2.stuid JOIN pets AS T3 ON T2.petid  =  T3.petid WHERE T3.pettype  =  'Cat' OR T3.pettype  =  'Dog'
SELECT T3.fname FROM has_pet AS T1 JOIN pets AS T2 ON T1.petid  =  T2.petid JOIN student AS T3 ON T3.stuid  =  T1.stuid WHERE T2.pettype  =  'Cat' INTERSECT SELECT T3.fname FROM has_pet AS T1 JOIN pets AS T2 ON T1.petid  =  T2.petid JOIN student AS T3 ON T3.stuid  =  T1.stuid WHERE T2.pettype  =  'Dog'
SELECT T1.fname FROM student AS T1 JOIN has_pet AS T2 ON T1.stuid  =  T2.stuid JOIN pets AS T3 ON T2.petid  =  T3.petid WHERE T3.pettype  =  'Cat' INTERSECT SELECT T1.fname FROM student AS T1 JOIN has_pet AS T2 ON T1.stuid  =  T2.stuid JOIN pets AS T3 ON T2.petid  =  T3.petid WHERE T3.pettype  =  'Dog'
SELECT major ,  age FROM student EXCEPT SELECT T1.major ,  T1.age FROM student AS T1 JOIN Has_pet AS T2 ON T1.stuid  =  T2.stuid JOIN pets AS T3 ON T2.petid  =  T3.petid WHERE T3.pettype  =  'Cat'
SELECT major ,  age FROM student WHERE stuid NOT IN (SELECT T1.stuid FROM student AS T1 JOIN Has_pet AS T2 ON T1.stuid  =  T2.stuid JOIN pets AS T3 ON T2.petid  =  T3.petid WHERE T3.pettype  =  'Cat')
SELECT StuID FROM Student EXCEPT SELECT T1.StuID FROM Student AS T1 JOIN Has_Pet AS T2 ON T1.StuID  =  T2.StuID JOIN Pets AS T3 ON T2.PetID  =  T3.PetID WHERE T3.PetType  =  'Cat'
SELECT StuID FROM student EXCEPT SELECT T1.StuID FROM student AS T1 JOIN Has_pet AS T2 ON T1.StuID  =  T2.StuID JOIN pets AS T3 ON T2.PetID  =  T3.PetID WHERE T3.PetType  =  "Cat"
SELECT DISTINCT T1.fname ,  T1.age FROM student AS T1 JOIN has_pet AS T2 ON T1.stuid  =  T2.stuid JOIN pets AS T3 ON T2.petid  =  T3.petid WHERE T3.pettype  =  'dog' EXCEPT SELECT DISTINCT T1.fname ,  T1.age FROM student AS T1 JOIN has_pet AS T2 ON T1.stuid  =  T2.stuid JOIN pets AS T3 ON T2.petid  =  T3.petid WHERE T3.pettype  =  'cat'
SELECT t1.fname FROM student AS t1 JOIN has_pet AS t2 ON t1.stuid  =  t2.stuid JOIN pets AS t3 ON t2.petid  =  t3.petid WHERE t3.pettype  =  'Dog' EXCEPT SELECT t1.fname FROM student AS t1 JOIN has_pet AS t2 ON t1.stuid  =  t2.stuid JOIN pets AS t3 ON t2.petid  =  t3.petid WHERE t3.pettype  =  'Cat'
SELECT pet_age ,  pettype ,  weight FROM pets ORDER BY weight LIMIT 1
SELECT pet_type ,  weight FROM pets ORDER BY pet_age LIMIT 1
SELECT pet_id ,  weight FROM pets WHERE pet_age  >  1
SELECT pet_id ,  weight FROM pets WHERE pet_age  >  1
SELECT avg(pet_age) ,  max(pet_age) ,  pettype FROM PETS GROUP BY pettype
SELECT avg(pet_age) ,  max(pet_age) ,  pettype FROM PETS GROUP BY pettype
SELECT avg(weight) ,  pettype FROM pets GROUP BY pettype
SELECT avg(weight) ,  pettype FROM pets GROUP BY pettype
SELECT DISTINCT T1.fname ,  T1.age FROM student AS T1 JOIN Has_pet AS T2 ON T1.StuID  =  T2.StuID
SELECT DISTINCT T1.fname ,  T1.age FROM student AS T1 JOIN Has_pet AS T2 ON T1.StuID  =  T2.StuID
SELECT DISTINCT T1.petid FROM student AS T1 JOIN Has_pet AS T2 ON T1.stuid  =  T2.stuid WHERE T1.lname  =  'Smith'
SELECT T2.petid FROM student AS T1 JOIN has_pet AS T2 ON T1.stuid  =  T2.stuid WHERE T1.lname  =  'Smith'
SELECT count(*) ,  StuID FROM Has_pet GROUP BY StuID
SELECT count(*) ,  T1.StuID FROM Student AS T1 JOIN Has_pet AS T2 ON T1.StuID  =  T2.StuID GROUP BY T1.StuID
SELECT t1.fname ,  t1.sex FROM student AS t1 JOIN has_pet AS t2 ON t1.stuid  =  t2.stuid GROUP BY t2.stuid HAVING count(*)  >  1
SELECT T1.fname ,  T1.sex FROM student AS T1 JOIN has_pet AS T2 ON T1.stuid  =  T2.stuid GROUP BY T2.stuid HAVING count(*)  >  1
SELECT t3.lname FROM has_pet AS t1 JOIN pets AS t2 ON t1.petid  =  t2.petid JOIN student AS t3 ON t1.stuid  =  t3.stuid WHERE t2.pet_age  =  3 AND t2.pettype  =  'Cat'
SELECT t1.lname FROM student AS t1 JOIN has_pet AS t2 ON t1.stuid  =  t2.stuid JOIN pets AS t3 ON t2.petid  =  t3.petid WHERE t3.pet_age  =  3 AND t3.pettype  =  'Cat'
SELECT avg(age) FROM student WHERE StuID NOT IN (SELECT StuID FROM Has_pet)
SELECT avg(age) FROM student WHERE StuID NOT IN (SELECT StuID FROM Has_pet)
SELECT count(*) FROM continents
SELECT count(*) FROM continents
SELECT T1.ContId ,  T1.Continent ,  COUNT(*) FROM continents AS T1 JOIN countries AS T2 ON T1.ContId  =  T2.Continent GROUP BY T1.ContId
SELECT ContId ,  Continent ,  COUNT(*) FROM countries GROUP BY Continent
SELECT count(*) FROM countries
SELECT count(*) FROM countries
SELECT T1.FullName ,  T1.Id ,  COUNT(*) FROM car_makers AS T1 JOIN model_list AS T2 ON T1.Id  =  T2.Maker GROUP BY T1.FullName ,  T1.Id
SELECT T1.id ,  T1.FullName ,  COUNT(*) FROM car_makers AS T1 JOIN model_list AS T2 ON T1.ID  =  T2.MAKER GROUP BY T1.ID
SELECT T1.Model FROM model_list AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId JOIN cars_data AS T3 ON T3.Id  =  T2.Id WHERE T3.Horsepower  =  (SELECT min(Horsepower) FROM cars_data)
SELECT T1.Model FROM car_names AS T1 JOIN cars_data AS T2 ON T1.MakeId  =  T2.Id ORDER BY T2.Horsepower ASC LIMIT 1
SELECT T1.Model FROM model_list AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId JOIN cars_data AS T3 ON T2.Id  =  T3.Id WHERE T3.Weight  <  (SELECT avg(Weight) FROM cars_data)
SELECT T1.Model FROM model_list AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId JOIN cars_data AS T3 ON T2.Id  =  T3.Id WHERE T3.weight  <  (SELECT avg(weight) FROM cars_data)
SELECT T2.Maker FROM cars_data AS T1 JOIN car_makers AS T2 ON T1.Id  =  T2.Id WHERE T1.Year  =  1970
SELECT T2.Maker FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId WHERE T1.Year  =  1970
SELECT T1.make ,  T1.Year FROM car_names AS T1 JOIN cars_data AS T2 ON T1.MakeId  =  T2.MakeId ORDER BY T1.Year ASC LIMIT 1
SELECT T2.Maker ,  T1.Year FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId ORDER BY T1.Year ASC LIMIT 1
SELECT DISTINCT T2.Model FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId WHERE T1.Year  >  1980;
SELECT DISTINCT T2.Model FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId WHERE T1.Year  >  1980
SELECT T1.Continent ,  count(*) FROM continents AS T1 JOIN countries AS T2 ON T1.ContId  =  T2.Continent JOIN car_makers AS T3 ON T3.Country  =  T2.CountryId GROUP BY T1.Continent
SELECT T1.Continent ,  COUNT(*) FROM continents AS T1 JOIN car_makers AS T2 ON T1.Continent  =  T2.Country GROUP BY T1.ContId
SELECT T2.CountryName FROM car_makers AS T1 JOIN countries AS T2 ON T1.Country  =  T2.CountryId GROUP BY T1.Country ORDER BY count(*) DESC LIMIT 1
SELECT T2.CountryName FROM car_makers AS T1 JOIN countries AS T2 ON T1.country  =  T2.CountryId GROUP BY T1.country ORDER BY count(*) DESC LIMIT 1
SELECT count(*) ,  T1.FullName FROM car_makers AS T1 JOIN model_list AS T2 ON T1.Id  =  T2.Maker GROUP BY T1.FullName
SELECT T2.Maker ,  count(*) FROM model_list AS T1 JOIN car_makers AS T2 ON T1.Maker  =  T2.Id GROUP BY T2.Maker UNION SELECT T2.Id ,  T2.FullName FROM model_list AS T1 JOIN car_makers AS T2 ON T1.Maker  =  T2.Id GROUP BY T2.Maker
SELECT t2.Accelerate FROM car_names AS t1 JOIN cars_data AS t2 ON t1.MakeId  =  t2.Id WHERE t1.Model  =  "amc hornet sportabout" AND t2.Year  =  "sw";
SELECT Accelerate FROM car_names AS T1 JOIN cars_data AS T2 ON T1.MakeId  =  T2.Id WHERE T1.Model  =  "amc hornet sportabout (sw)"
SELECT count(*) FROM car_makers WHERE Country  =  "France"
SELECT count(*) FROM car_makers WHERE Country  =  "France"
SELECT count(*) FROM car_makers WHERE Country  =  "USA";
SELECT count(*) FROM car_makers AS T1 JOIN model_list AS T2 ON T1.id  =  T2.maker WHERE T1.country  =  "United States"
SELECT avg(MPG) FROM cars_data WHERE Cylinders  =  4
SELECT avg(mpg) FROM cars_data WHERE Cylinders  =  4
SELECT min(weight) FROM cars_data WHERE cylinders  =  8 AND YEAR  =  1974;
SELECT min(weight) FROM cars_data WHERE cylinders  =  8 AND YEAR  =  1974
SELECT DISTINCT T2.Maker ,  T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.Model  =  T2.Model
SELECT T2.Maker ,  T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.Model  =  T2.Model
SELECT T1.CountryName ,  T1.CountryId FROM countries AS T1 JOIN car_makers AS T2 ON T1.CountryId  =  T2.Country
SELECT T1.CountryName ,  T1.CountryId FROM countries AS T1 JOIN car_makers AS T2 ON T1.CountryId  =  T2.Country
SELECT count(*) FROM cars_data WHERE Horsepower  >  150
SELECT count(*) FROM cars_data WHERE horsepower  >  150
SELECT YEAR ,  avg(Weight) FROM cars_data GROUP BY YEAR
SELECT avg(Weight) ,  YEAR FROM cars_data GROUP BY YEAR
SELECT T2.CountryName FROM car_makers AS T1 JOIN countries AS T2 ON T1.Country  =  T2.CountryId WHERE T2.Continent  =  "Europe" GROUP BY T2.CountryName HAVING COUNT(*)  >=  3
SELECT T2.CountryName FROM car_makers AS T1 JOIN countries AS T2 ON T1.Country  =  T2.CountryId WHERE T2.Continent  =  "Europe" GROUP BY T2.CountryName HAVING COUNT(*)  >=  3
SELECT T1.Horsepower ,  T2.Model FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId WHERE T1.Cylinders  =  3 ORDER BY T1.Horsepower DESC LIMIT 1
SELECT T1.Horsepower ,  T2.Maker FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId WHERE T1.Cylinders  =  3 ORDER BY T1.Horsepower DESC LIMIT 1
SELECT T1.Model FROM model_list AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId JOIN cars_data AS T3 ON T2.Id  =  T3.Id WHERE T3.MPG  =  (SELECT max(MPG) FROM cars_data)
SELECT T2.Model FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId ORDER BY T1.MPG DESC LIMIT 1
SELECT avg(horsepower) FROM cars_data WHERE YEAR  <  1980
SELECT avg(horsepower) FROM cars_data WHERE YEAR  <  1980
SELECT avg(T1.Edispl) FROM car_names AS T2 JOIN cars_data AS T1 ON T1.Id  =  T2.MakeId JOIN model_list AS T3 ON T2.Model  =  T3.Model WHERE T3.Model  =  "volvo"
SELECT avg(edispl) FROM car_names AS T1 JOIN cars_data AS T2 ON T1.MakeId  =  T2.MakeId WHERE T1.Model  =  'volvo'
SELECT max(Accelerate) ,  Cylinders FROM cars_data GROUP BY Cylinders
SELECT max(Accelerate) ,  Cylinders FROM cars_data GROUP BY Cylinders
SELECT T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.Model  =  T2.Model GROUP BY T2.Model ORDER BY COUNT(*) DESC LIMIT 1
SELECT T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.Model  =  T2.Model GROUP BY T2.Model ORDER BY COUNT(*) DESC LIMIT 1
SELECT count(*) FROM cars_data WHERE Cylinders  >  4
SELECT count(*) FROM cars_data WHERE Cylinders  >  4
SELECT count(*) FROM cars_data WHERE YEAR  =  1980
SELECT count(*) FROM cars_data WHERE YEAR  =  1980
SELECT count(*) FROM model_list AS T1 JOIN car_makers AS T2 ON T1.Maker  =  T2.Id WHERE T2.FullName  =  "American Motor Company"
SELECT count(*) FROM model_list WHERE Maker  =  "American Motor Company"
SELECT T1.id ,  T1.FullName FROM car_makers AS T1 JOIN model_list AS T2 ON T1.id  =  T2.Maker GROUP BY T1.id HAVING count(*)  >  3;
SELECT T1.Maker ,  T1.Id FROM car_makers AS T1 JOIN model_list AS T2 ON T1.Id  =  T2.Maker GROUP BY T1.Maker HAVING COUNT(*)  >  3;
SELECT DISTINCT T2.Model FROM car_names AS T2 JOIN cars_data AS T1 ON T2.Make  =  T1.Id JOIN car_makers AS T3 ON T3.Id  =  T2.MakeId WHERE T3.FullName  =  "General Motors" AND T1.Weight  >  3500;
SELECT DISTINCT T2.Model FROM car_names AS T2 JOIN cars_data AS T1 ON T2.Make  =  T1.Id JOIN car_makers AS T3 ON T3.Id  =  T2.MakeId WHERE T3.Maker  =  "General Motors" UNION SELECT DISTINCT T2.Model FROM car_names AS T2 JOIN cars_data AS T1 ON T2.Make  =  T1.Id WHERE T1.Weight  >  3500
SELECT YEAR FROM cars_data WHERE Weight BETWEEN 3000 AND 4000
SELECT DISTINCT YEAR FROM cars_data WHERE Weight  <  4000 INTERSECT SELECT DISTINCT YEAR FROM cars_data WHERE Weight  >  3000
SELECT Horsepower FROM cars_data ORDER BY Accelerate DESC LIMIT 1
SELECT Horsepower FROM cars_data ORDER BY Accelerate DESC LIMIT 1
SELECT cylinders FROM car_names AS T1 JOIN cars_data AS T2 ON T1.MakeId  =  T2.Id WHERE T1.Model  =  "volvo" ORDER BY T2.Accelerate ASC LIMIT 1
SELECT cylinders FROM car_names WHERE model  =  "volvo" JOIN cars_data ON car_names.makeid  =  cars_data.id ORDER BY cars_data.accelerate ASC LIMIT 1
SELECT count(*) FROM cars_data WHERE Accelerate  >  ( SELECT max(Accelerate) FROM cars_data WHERE Horsepower  =  ( SELECT max(Horsepower) FROM cars_data ) )
SELECT count(*) FROM cars_data WHERE Accelerate  >  ( SELECT max(Horsepower) FROM cars_data )
SELECT COUNT(*) FROM car_makers GROUP BY Country HAVING COUNT(*)  >  2
SELECT count(*) FROM car_makers GROUP BY Country HAVING count(*)  >  2
SELECT count(*) FROM cars_data WHERE Cylinders  >  6
SELECT count(*) FROM cars_data WHERE Cylinders  >  6
SELECT T2.Model FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId WHERE T1.Cylinders  =  4 ORDER BY T1.Horsepower DESC LIMIT 1
SELECT T2.Model FROM cars_data AS T1 JOIN car_names AS T2 ON T1.Id  =  T2.MakeId WHERE T1.Cylinders  =  4 ORDER BY T1.Horsepower DESC LIMIT 1
SELECT T1.id ,  T2.make FROM cars_data AS T1 JOIN car_names AS T2 ON T1.id  =  T2.make WHERE T1.horsepower  >  CONCAT('select min(horsepower) FROM cars_data') AND T1.cylinders  >  3;
SELECT T1.id ,  T1.model FROM car_names AS T1 JOIN cars_data AS T2 ON T1.id  =  T2.id WHERE T2.cylinders  <  4 EXCEPT SELECT T1.id ,  T1.model FROM car_names AS T1 JOIN cars_data AS T2 ON T1.id  =  T2.id WHERE T2.horsepower  =  ( SELECT min(horsepower) FROM cars_data )
SELECT max(MPG) FROM cars_data WHERE Cylinders  =  8 OR YEAR  <  1980;
SELECT max(MPG) FROM cars_data WHERE Cylinders  =  8 OR YEAR  <  1980;
SELECT T2.model FROM car_names AS T1 JOIN model_list AS T2 ON T1.Model  =  T2.Model JOIN cars_data AS T3 ON T3.Id  =  T1.Make WHERE T3.Weight  <  3500 EXCEPT SELECT T2.model FROM car_names AS T1 JOIN model_list AS T2 ON T1.Model  =  T2.Model JOIN cars_data AS T3 ON T3.Id  =  T1.Make WHERE T2.Maker  =  'Ford Motor Company'
SELECT DISTINCT T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.Model  =  T2.Model JOIN cars_data AS T3 ON T3.Id  =  T1.Make WHERE T3.Weight  <  3500 EXCEPT SELECT DISTINCT T2.Model FROM car_names AS T1 JOIN model_list AS T2 ON T1.Model  =  T2.Model JOIN cars_data AS T3 ON T3.Id  =  T1.Make WHERE T2.Maker  =  "Ford Motor Company"
SELECT CountryName FROM countries EXCEPT SELECT T2.CountryName FROM car_makers AS T1 JOIN countries AS T2 ON T1.Country  =  T2.CountryId GROUP BY T1.Country
SELECT CountryName FROM countries WHERE CountryId NOT IN (SELECT Country FROM car_makers)
SELECT T1.id , T1.maker FROM car_makers AS T1 JOIN model_list AS T2 ON T1.id  =  T2.maker GROUP BY T1.id HAVING count(*)  >=  2 INTERSECT SELECT T1.id , T1.maker FROM car_makers AS T1 JOIN model_list AS T2 ON T1.id  =  T2.maker GROUP BY T1.id HAVING count(*)  >  3
SELECT T1.id ,  T1.maker FROM car_makers AS T1 JOIN model_list AS T2 ON T1.id  =  T2.maker JOIN car_names AS T3 ON T3.Make  =  T2.Model WHERE T2.Model IN ( SELECT T2.Model FROM car_makers AS T1 JOIN model_list AS T2 ON T1.id  =  T2.maker JOIN car_names AS T3 ON T3.Make  =  T2.Model GROUP BY T2.Model HAVING COUNT ( DISTINCT T2.Model )  >=  2 ) GROUP BY T1.id HAVING COUNT ( DISTINCT T3.Model )  >=  3
SELECT T2.CountryId ,  T2.CountryName FROM car_makers AS T1 JOIN countries AS T2 ON T1.Country  =  T2.CountryId GROUP BY T2.CountryId HAVING COUNT(*)  >  3 UNION SELECT T2.CountryId ,  T2.CountryName FROM car_names AS T3 JOIN cars_data AS T4 ON T3.Make  =  T4.Id JOIN countries AS T2 ON T2.CountryId  =  T1.Country GROUP BY T2.CountryId HAVING T3.Model  =  'fiat'
SELECT T2.CountryId ,  T2.CountryName FROM car_makers AS T1 JOIN countries AS T2 ON T1.Country  =  T2.CountryId JOIN model_list AS T3 ON T1.Maker  =  T3.Maker WHERE T3.Model  =  "Fiesta" GROUP BY T2.CountryName HAVING COUNT(*)  >  3 UNION SELECT T2.CountryId ,  T2.CountryName FROM car_makers AS T1 JOIN countries AS T2 ON T1.Country  =  T2.CountryId GROUP BY T2.CountryName HAVING COUNT(*)  >  3
SELECT Country FROM airlines WHERE Airline  =  "JetBlue Airways"
SELECT Country FROM airlines WHERE Airline  =  "Jetblue Airways"
SELECT Abbreviation FROM airlines WHERE Airline  =  "JetBlue Airways"
SELECT Abbreviation FROM airlines WHERE Airline  =  "Jetblue Airways"
SELECT Airline ,  Abbreviation FROM airlines WHERE Country  =  "USA"
SELECT Airline ,  Abbreviation FROM airlines WHERE Country  =  'USA'
SELECT AirportCode ,  AirportName FROM airports WHERE City  =  "Anthony"
SELECT AirportCode ,  AirportName FROM airports WHERE City  =  "Anthony"
SELECT count(*) FROM airlines
SELECT count(*) FROM airlines
SELECT count(*) FROM airports
SELECT count(*) FROM airports
SELECT count(*) FROM flights
SELECT count(*) FROM flights
SELECT Airline FROM airlines WHERE Abbreviation  =  'UAL'
SELECT Airline FROM airlines WHERE Abbreviation  =  'UAL'
SELECT count(*) FROM airlines WHERE country  =  'USA'
SELECT count(*) FROM airlines WHERE country  =  'United States'
SELECT city ,  country FROM airports WHERE AirportName  =  "Alton Airport"
SELECT city ,  country FROM airports WHERE AirportName  =  "Alton Airport"
SELECT AirportName FROM airports WHERE AirportCode  =  'AKO'
SELECT AirportName FROM airports WHERE AirportCode  =  'AKO'
SELECT AirportName FROM airports WHERE City  =  'Aberdeen'
SELECT AirportName FROM airports WHERE City  =  "Aberdeen"
SELECT count(*) FROM flights WHERE sourceairport  =  'APG'
SELECT count(*) FROM flights WHERE sourceairport  =  'APG'
SELECT count(*) FROM flights WHERE DestAirport  =  "ATO"
SELECT count(*) FROM flights WHERE destairport  =  'ATO'
SELECT count(*) FROM airports AS T1 JOIN flights AS T2 ON T1.AirportCode  =  T2.SourceAirport WHERE T1.City  =  "Aberdeen"
SELECT count(*) FROM airports AS T1 JOIN flights AS T2 ON T1.AirportCode  =  T2.SourceAirport WHERE T1.City  =  "Aberdeen"
SELECT count(*) FROM airports AS T1 JOIN flights AS T2 ON T1.AirportCode  =  T2.DestAirport WHERE T1.City  =  "Aberdeen"
SELECT count(*) FROM airports AS T1 JOIN flights AS T2 ON T1.AirportCode  =  T2.DestAirport WHERE T1.AirportName  =  "Aberdeen"
SELECT count(*) FROM airports AS T1 JOIN flights AS T2 ON T1.AirportCode  =  T2.DestAirport WHERE T1.City  =  'Aberdeen' AND T2.DestAirport  =  'Ashley'
SELECT count(*) FROM flights WHERE sourceairport  =  'Aberdeen' AND destairport  =  'Ashley'
SELECT count(*) FROM flights WHERE airline  =  'JetBlue Airways'
SELECT count(*) FROM flights WHERE airline  =  "Jetblue Airways"
SELECT count(*) FROM flights AS T1 JOIN airports AS T2 ON T1.DestAirport  =  T2.AirportCode WHERE T2.AirportName  =  "ASY" AND T1.Airline  =  "United Airlines"
SELECT count(*) FROM flights AS T1 JOIN airports AS T2 ON T1.DestAirport  =  T2.AirportCode WHERE T2.AirportName  =  "ASY" AND T1.Airline  =  "United Airlines"
SELECT count(*) FROM flights AS T1 JOIN airports AS T2 ON T1.SourceAirport  =  T2.AirportCode WHERE T2.AirportName  =  'AHD' AND T1.Airline  =  'United Airlines'
SELECT count(*) FROM flights AS T1 JOIN airports AS T2 ON T1.SourceAirport  =  T2.AirportCode WHERE T2.AirportName  =  "Ahd" AND T1.Airline  =  "United Airlines"
SELECT count(*) FROM flights AS T1 JOIN airports AS T2 ON T1.DestAirport  =  T2.AirportCode WHERE T2.City  =  'Aberdeen' AND T1.Airline  =  'United Airlines'
SELECT count(*) FROM flights AS T1 JOIN airports AS T2 ON T1.DestAirport  =  T2.AirportCode WHERE T2.City  =  "Aberdeen" AND T1.Airline  =  "United Airlines"
SELECT T1.City FROM airports AS T1 JOIN flights AS T2 ON T1.AirportCode  =  T2.DestAirport GROUP BY T2.DestAirport ORDER BY count(*) DESC LIMIT 1
SELECT T1.City FROM airports AS T1 JOIN flights AS T2 ON T1.AirportCode  =  T2.DestAirport GROUP BY T2.DestAirport ORDER BY count(*) DESC LIMIT 1
SELECT T1.City FROM airports AS T1 JOIN flights AS T2 ON T1.AirportCode  =  T2.SourceAirport GROUP BY T2.SourceAirport ORDER BY count(*) DESC LIMIT 1
SELECT T1.City FROM airports AS T1 JOIN flights AS T2 ON T1.AirportCode  =  T2.SourceAirport GROUP BY T2.SourceAirport ORDER BY count(*) DESC LIMIT 1
SELECT T1.AirportCode FROM airports AS T1 JOIN flights AS T2 ON T1.AirportCode  =  T2.DestAirport GROUP BY T2.DestAirport ORDER BY count(*) DESC LIMIT 1
SELECT DestAirport FROM flights GROUP BY DestAirport ORDER BY count(*) DESC LIMIT 1
SELECT DestAirport FROM flights GROUP BY DestAirport ORDER BY count(*) LIMIT 1
SELECT DestAirport FROM flights GROUP BY DestAirport ORDER BY count(*) ASC LIMIT 1
SELECT airline FROM flights GROUP BY airline ORDER BY count(*) DESC LIMIT 1
SELECT airline FROM flights GROUP BY airline ORDER BY count(*) DESC LIMIT 1
SELECT T1.Abbreviation ,  T1.Country FROM airlines AS T1 JOIN flights AS T2 ON T1.Airline  =  T2.Airline GROUP BY T2.Airline ORDER BY count(*) ASC LIMIT 1
SELECT T1.Abbreviation ,  T1.Country FROM airlines AS T1 JOIN flights AS T2 ON T1.Airline  =  T2.Airline GROUP BY T2.Airline ORDER BY count(*) LIMIT 1
SELECT Airline FROM flights WHERE SourceAirport  =  'AHD'
SELECT Airline FROM flights WHERE SourceAirport  =  "AHD"
SELECT T1.Airline FROM flights AS T1 JOIN airports AS T2 ON T1.DestAirport  =  T2.AirportCode WHERE T2.AirportName  =  'AHD'
SELECT Airline FROM flights WHERE DestAirport  =  "AHD"
SELECT Airline FROM flights WHERE SourceAirport  =  'APG' INTERSECT SELECT Airline FROM flights WHERE SourceAirport  =  'CVO'
SELECT Airline FROM flights WHERE SourceAirport  =  'APG' INTERSECT SELECT Airline FROM flights WHERE SourceAirport  =  'CVO'
SELECT Airline FROM flights WHERE SourceAirport  =  'CVO' EXCEPT SELECT Airline FROM flights WHERE SourceAirport  =  'APG'
SELECT Airline FROM flights WHERE SourceAirport  =  'CVO' EXCEPT SELECT Airline FROM flights WHERE SourceAirport  =  'APG'
SELECT Airline FROM flights GROUP BY Airline HAVING count(*)  >=  10
SELECT Airline FROM flights GROUP BY Airline HAVING count(*)  >=  10
SELECT Airline FROM flights GROUP BY Airline HAVING count(*)  <  200
SELECT Airline FROM flights GROUP BY Airline HAVING count(*)  <  200
SELECT FlightNo FROM flights WHERE Airline  =  "United Airlines"
SELECT FlightNo FROM flights WHERE Airline  =  "United Airlines"
SELECT FlightNo FROM flights WHERE SourceAirport  =  "APG"
SELECT FlightNo FROM flights WHERE SourceAirport  =  "APG"
SELECT FlightNo FROM flights WHERE DestAirport  =  "APG"
SELECT FlightNo FROM flights WHERE DestAirport  =  "APG"
SELECT T2.FlightNo FROM airports AS T1 JOIN flights AS T2 ON T1.AirportCode  =  T2.SourceAirport WHERE T1.City  =  "Aberdeen"
SELECT T1.FlightNo FROM flights AS T1 JOIN airports AS T2 ON T1.SourceAirport  =  T2.AirportCode WHERE T2.AirportName  =  "Aberdeen"
SELECT T1.FlightNo FROM flights AS T1 JOIN airports AS T2 ON T1.DestAirport  =  T2.AirportCode WHERE T2.City  =  "Aberdeen"
SELECT T1.FlightNo FROM flights AS T1 JOIN airports AS T2 ON T1.DestAirport  =  T2.AirportCode WHERE T2.AirportName  =  "Abderdeen"
SELECT count(*) FROM airports AS T1 JOIN flights AS T2 ON T1.AirportCode  =  T2.DestAirport WHERE T1.City  =  "Aberdeen" OR T1.City  =  "Abilene"
SELECT count(*) FROM airports WHERE AirportName  =  "Aberdeen" OR AirportName  =  "Abilene"
SELECT AirportName FROM airports WHERE AirportCode NOT IN (SELECT DestAirport FROM flights UNION SELECT SourceAirport FROM flights)
SELECT AirportName FROM airports WHERE AirportCode NOT IN (SELECT DestAirport FROM flights UNION SELECT SourceAirport FROM flights)
SELECT count(*) FROM employee
SELECT count(*) FROM employee
SELECT name FROM employee ORDER BY age ASC
SELECT name FROM employee ORDER BY age ASC
SELECT count(*) ,  city FROM employee GROUP BY city
SELECT count(*) ,  city FROM employee GROUP BY city
SELECT city FROM employee WHERE age  <  30 GROUP BY city HAVING count(*)  >  1
SELECT city FROM employee WHERE age  <  30 GROUP BY city HAVING count(*)  >  1
SELECT count(*) ,  LOCATION FROM shop GROUP BY LOCATION
SELECT LOCATION ,  count(*) FROM shop GROUP BY LOCATION
SELECT manager_name ,  district FROM shop ORDER BY number_products DESC LIMIT 1
SELECT manager_name ,  district FROM shop ORDER BY number_products DESC LIMIT 1
SELECT min(number_products) ,  max(number_products) FROM shop
SELECT min(number_products) ,  max(number_products) FROM shop
SELECT name ,  LOCATION ,  district FROM shop ORDER BY Number_products DESC
SELECT name ,  LOCATION ,  district FROM shop ORDER BY Number_products DESC
SELECT name FROM shop WHERE number_products  >  (SELECT avg(number_products) FROM shop)
SELECT name FROM shop WHERE number_products  >  (SELECT avg(number_products) FROM shop)
SELECT T1.name FROM employee AS T1 JOIN evaluation AS T2 ON T1.employee_id  =  T2.employee_id GROUP BY T2.employee_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.name FROM employee AS T1 JOIN evaluation AS T2 ON T1.employee_id  =  T2.employee_id GROUP BY T2.employee_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.name FROM employee AS T1 JOIN evaluation AS T2 ON T1.employee_id  =  T2.employee_id ORDER BY bonus LIMIT 1
SELECT T1.name FROM employee AS T1 JOIN evaluation AS T2 ON T1.employee_id  =  T2.employee_id ORDER BY bonus DESC LIMIT 1
SELECT name FROM employee WHERE employee_id NOT IN (SELECT employee_id FROM evaluation)
SELECT name FROM employee WHERE employee_id NOT IN (SELECT employee_id FROM evaluation)
SELECT T2.name FROM hiring AS T1 JOIN shop AS T2 ON T1.shop_id  =  T2.shop_id GROUP BY T1.shop_id ORDER BY count(*) DESC LIMIT 1
SELECT name FROM shop ORDER BY number_products DESC LIMIT 1
SELECT name FROM shop WHERE shop_id NOT IN (SELECT shop_id FROM hiring)
SELECT name FROM shop WHERE shop_id NOT IN (SELECT shop_id FROM hiring)
SELECT count(*) ,  T1.name FROM shop AS T1 JOIN hiring AS T2 ON T1.shop_id  =  T2.shop_id GROUP BY T1.shop_id
SELECT count(*) ,  T1.name FROM shop AS T1 JOIN hiring AS T2 ON T1.shop_id  =  T2.shop_id GROUP BY T1.shop_id
SELECT sum(bonus) FROM evaluation
SELECT sum(bonus) FROM evaluation
SELECT * FROM hiring
SELECT * FROM hiring
SELECT district FROM shop WHERE number_products  <  3000 INTERSECT SELECT district FROM shop WHERE number_products  >  10000
SELECT district FROM shop WHERE number_products  <  3000 INTERSECT SELECT district FROM shop WHERE number_products  >  10000
SELECT count(DISTINCT LOCATION) FROM shop
SELECT count(DISTINCT LOCATION) FROM shop
SELECT count(*) FROM Documents
SELECT count(*) FROM Documents
SELECT document_id ,  document_name ,  document_description FROM Documents
SELECT document_id ,  document_name ,  document_description FROM Documents
SELECT document_name ,  template_id FROM Documents WHERE Document_Description LIKE '%w%'
SELECT document_name ,  template_id FROM Documents WHERE Document_description LIKE "%w%"
SELECT document_id ,  template_id ,  document_description FROM Documents WHERE document_name  =  "Robbin CV"
SELECT document_id ,  template_id ,  document_description FROM Documents WHERE document_name  =  "Robbin CV"
SELECT count(DISTINCT template_id) FROM documents
SELECT count(DISTINCT template_id) FROM documents
SELECT count(*) FROM Documents AS T1 JOIN Templates AS T2 ON T1.template_id  =  T2.template_id WHERE T2.template_type_code  =  "PPT"
SELECT count(*) FROM Documents AS T1 JOIN Templates AS T2 ON T1.template_id  =  T2.template_id WHERE T2.template_type_code  =  "PPT"
SELECT template_id ,  count(*) FROM Documents GROUP BY template_id
SELECT Template_ID ,  count(*) FROM Documents GROUP BY Template_ID
SELECT T1.template_id ,  T1.template_type_code FROM Templates AS T1 JOIN Documents AS T2 ON T1.template_id  =  T2.template_id GROUP BY T1.template_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.Template_ID ,  T1.Template_Type_Code FROM Templates AS T1 JOIN Documents AS T2 ON T1.Template_ID  =  T2.Template_ID GROUP BY T1.Template_ID ORDER BY COUNT(*) DESC LIMIT 1
SELECT template_id FROM Documents GROUP BY template_id HAVING count(*)  >  1
SELECT template_id FROM Documents GROUP BY template_id HAVING count(*)  >  1
SELECT template_id FROM Templates EXCEPT SELECT template_id FROM Documents
SELECT Template_ID FROM Templates EXCEPT SELECT Template_ID FROM Documents
SELECT count(*) FROM Templates
SELECT count(*) FROM Templates
SELECT template_id ,  version_number ,  template_type_code FROM Templates
SELECT template_id ,  version_number ,  template_type_code FROM Templates
SELECT DISTINCT template_type_code FROM templates
SELECT DISTINCT template_type_code FROM Ref_Template_Types
SELECT template_id FROM Templates WHERE template_type_code  =  "PP" OR template_type_code  =  "PPT"
SELECT template_id FROM Templates WHERE template_type_code  =  "PP" OR template_type_code  =  "PPT"
SELECT count(*) FROM Templates WHERE template_type_code  =  "CV"
SELECT count(*) FROM Templates AS T JOIN Ref_Template_Types AS TT ON T.template_type_code  =  TT.template_type_code WHERE TT.template_type_code  =  "CV"
SELECT version_number ,  template_type_code FROM Templates WHERE Version_Number  >  5
SELECT version_number ,  template_type_code FROM Templates WHERE version_number  >  5
SELECT template_type_code ,  count(*) FROM Templates GROUP BY template_type_code
SELECT template_type_code ,  count(*) FROM Templates GROUP BY template_type_code
SELECT template_type_code FROM templates GROUP BY template_type_code ORDER BY count(*) DESC LIMIT 1
SELECT template_type_code FROM Templates GROUP BY template_type_code ORDER BY count(*) DESC LIMIT 1
SELECT template_type_code FROM Templates GROUP BY template_type_code HAVING count(*)  <  3
SELECT template_type_code FROM Templates GROUP BY template_type_code HAVING count(*)  <  3
SELECT min(version_number) ,  template_type_code FROM Templates GROUP BY template_type_code
SELECT min(version_number) ,  template_type_code FROM Templates GROUP BY template_type_code
SELECT T2.Template_Type_Code FROM Documents AS T1 JOIN Templates AS T2 ON T1.Template_ID  =  T2.Template_ID WHERE T1.Document_Name  =  "Data base"
SELECT T2.Template_Type_Code FROM Documents AS T1 JOIN Templates AS T2 ON T1.Template_ID  =  T2.Template_ID WHERE T1.Document_Name  =  "Data base"
SELECT T2.Document_Name FROM Templates AS T1 JOIN Documents AS T2 ON T1.Template_ID  =  T2.Template_ID WHERE T1.Template_Type_Code  =  "BK"
SELECT T1.Document_Name FROM Documents AS T1 JOIN Templates AS T2 ON T1.Template_ID  =  T2.Template_ID WHERE T2.Template_Type_Code  =  "BK"
SELECT T2.Template_Type_Code ,  count(*) FROM Documents AS T1 JOIN Templates AS T2 ON T1.Template_ID  =  T2.Template_ID GROUP BY T2.Template_Type_Code
SELECT T2.Template_Type_Code ,  count(*) FROM Documents AS T1 JOIN Templates AS T2 ON T1.Template_ID  =  T2.Template_ID GROUP BY T2.Template_Type_Code
SELECT T2.template_type_code FROM Documents AS T1 JOIN Templates AS T2 ON T1.template_id  =  T2.template_id GROUP BY T2.template_type_code ORDER BY count(*) DESC LIMIT 1
SELECT T2.template_type_code FROM templates AS T1 JOIN Ref_Template_Types AS T2 ON T1.template_type_code  =  T2.template_type_code GROUP BY T1.template_type_code ORDER BY count(*) DESC LIMIT 1
SELECT template_type_code FROM Ref_template_types EXCEPT SELECT template_type_code FROM Templates
SELECT template_type_code FROM Ref_Template_Types EXCEPT SELECT template_type_code FROM Templates
SELECT template_type_code ,  template_type_description FROM Ref_Template_Types
SELECT template_type_code ,  template_type_description FROM Ref_Template_Types
SELECT template_type_description FROM Ref_Template_Types WHERE template_type_code  =  "AD"
SELECT template_type_description FROM Ref_Template_Types WHERE template_type_code  =  "AD"
SELECT template_type_code FROM Ref_Template_Types WHERE template_type_description  =  "Book"
SELECT template_type_code FROM Ref_Template_Types WHERE template_type_description  =  "Book"
SELECT DISTINCT T2.Template_Type_Description FROM Documents AS T1 JOIN Ref_Template_Types AS T2 ON T1.Template_Type_Code  =  T2.Template_Type_Code
SELECT DISTINCT T2.Template_Type_Description FROM Documents AS T1 JOIN Ref_Template_Types AS T2 ON T1.template_id  =  T2.template_type_code
SELECT T2.Template_ID FROM Ref_Template_Types AS T1 JOIN Templates AS T2 ON T1.Template_Type_Code  =  T2.Template_Type_Code WHERE T1.Template_Type_Description  =  "Presentation"
SELECT template_id FROM Templates AS T JOIN Ref_Template_Types AS R ON T.template_type_code  =  R.template_type_code WHERE R.template_type_description  =  "Presentation"
SELECT count(*) FROM Paragraphs
SELECT count(*) FROM Paragraphs
SELECT count(*) FROM Paragraphs AS T1 JOIN Documents AS T2 ON T1.document_id  =  T2.document_id WHERE T2.document_name  =  "Summer Show"
SELECT count(*) FROM Paragraphs AS T1 JOIN Documents AS T2 ON T1.document_id  =  T2.document_id WHERE T2.document_name  =  "Summer Show"
SELECT other_details FROM Paragraphs WHERE paragraph_text  =  "Korea"
SELECT Other_Details FROM Paragraphs WHERE Paragraph_Text LIKE '%Korea%'
SELECT t1.paragraph_id ,  t1.paragraph_text FROM Paragraphs AS t1 JOIN Documents AS t2 ON t1.document_id  =  t2.document_id WHERE t2.document_name  =  "Welcome to NY"
SELECT t1.paragraph_id ,  t1.paragraph_text FROM Paragraphs AS t1 JOIN Documents AS t2 ON t1.document_id  =  t2.document_id WHERE t2.document_name  =  "Welcome to NY"
SELECT t2.Paragraph_Text FROM Documents AS t1 JOIN Paragraphs AS t2 ON t1.Document_ID  =  t2.Document_ID WHERE t1.Document_Name  =  "Customer reviews"
SELECT T2.Paragraph_Text FROM Documents AS T1 JOIN Paragraphs AS T2 ON T1.Document_ID  =  T2.Document_ID WHERE T1.Document_Name  =  "Customer reviews"
SELECT T1.document_id ,  count(*) FROM Documents AS T1 JOIN Paragraphs AS T2 ON T1.document_id  =  T2.document_id GROUP BY T1.document_id ORDER BY T1.document_id
SELECT document_id ,  count(*) FROM Paragraphs GROUP BY document_id ORDER BY document_id
SELECT T1.document_id ,  T1.document_name ,  count(*) FROM Documents AS T1 JOIN Paragraphs AS T2 ON T1.document_id  =  T2.document_id GROUP BY T1.document_id
SELECT T1.document_id ,  T1.document_name ,  (SELECT count(*) FROM Paragraphs AS T2 WHERE T2.document_id  =  T1.document_id) FROM Documents AS T1
SELECT document_id FROM Paragraphs GROUP BY document_id HAVING count(*)  >=  2
SELECT document_id FROM Paragraphs GROUP BY document_id HAVING count(*)  >=  2
SELECT T1.document_id ,  T1.document_name FROM Documents AS T1 JOIN Paragraphs AS T2 ON T1.document_id  =  T2.document_id GROUP BY T1.document_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.document_id ,  T1.document_name FROM Documents AS T1 JOIN Paragraphs AS T2 ON T1.document_id  =  T2.document_id GROUP BY T1.document_id ORDER BY count(*) DESC LIMIT 1
SELECT document_id FROM Paragraphs GROUP BY document_id ORDER BY count(*) ASC LIMIT 1
SELECT document_id FROM Paragraphs GROUP BY document_id ORDER BY count(*) ASC LIMIT 1
SELECT document_id FROM Paragraphs GROUP BY document_id HAVING count(*) BETWEEN 1 AND 2
SELECT document_id FROM Paragraphs GROUP BY document_id HAVING count(*) BETWEEN 1 AND 2
SELECT t1.document_id FROM Paragraphs AS t1 JOIN Paragraphs AS t2 ON t1.document_id  =  t2.document_id WHERE t1.Paragraph_Text  =  'Brazil' AND t2.Paragraph_Text  =  'Ireland'
SELECT T1.document_id FROM Paragraphs AS T1 JOIN Paragraphs AS T2 ON T1.document_id  =  T2.document_id WHERE T1.Paragraph_Text  =  'Brazil' AND T2.Paragraph_Text  =  'Ireland'
SELECT count(*) FROM teacher
SELECT count(*) FROM teacher
SELECT Name FROM teacher ORDER BY Age ASC
SELECT Name FROM teacher ORDER BY Age ASC
SELECT Age ,  Hometown FROM teacher
SELECT Age ,  Hometown FROM teacher
SELECT Name FROM teacher WHERE Hometown != "Little Lever Urban District"
SELECT Name FROM teacher WHERE Hometown != "Little Lever Urban District"
SELECT Name FROM teacher WHERE Age  =  32 OR Age  =  33
SELECT Name FROM teacher WHERE Age  =  32 OR Age  =  33
SELECT Hometown FROM teacher ORDER BY Age ASC LIMIT 1
SELECT Hometown FROM teacher ORDER BY Age ASC LIMIT 1
SELECT Hometown ,  COUNT(*) FROM teacher GROUP BY Hometown
SELECT Hometown ,  COUNT(*) FROM teacher GROUP BY Hometown
SELECT Hometown FROM teacher GROUP BY Hometown ORDER BY COUNT(*) DESC LIMIT 1
SELECT Hometown FROM teacher GROUP BY Hometown ORDER BY COUNT(*) DESC LIMIT 1
SELECT Hometown FROM teacher GROUP BY Hometown HAVING COUNT(*)  >=  2
SELECT Hometown FROM teacher GROUP BY Hometown HAVING COUNT(*)  >=  2
SELECT T2.Name ,  T1.Course FROM course_arrange AS T1 JOIN teacher AS T2 ON T1.Teacher_ID  =  T2.Teacher_ID
SELECT T2.Name ,  T1.Course FROM course AS T1 JOIN teacher AS T2 ON T1.Course_ID  =  T2.Teacher_ID
SELECT T2.Name ,  T1.Course FROM course_arrange AS T1 JOIN teacher AS T2 ON T1.Teacher_ID  =  T2.Teacher_ID ORDER BY T2.Name ASC
SELECT T2.Name ,  T1.Course FROM course AS T1 JOIN teacher AS T2 ON T1.Teacher_ID  =  T2.Teacher_ID ORDER BY T2.Name ASC
SELECT T2.Name FROM course_arrange AS T1 JOIN teacher AS T2 ON T1.Teacher_ID  =  T2.Teacher_ID JOIN course AS T3 ON T1.Course_ID  =  T3.Course_ID WHERE T3.Course  =  "Math"
SELECT T2.Name FROM course_arrange AS T1 JOIN teacher AS T2 ON T1.Teacher_ID  =  T2.Teacher_ID JOIN course AS T3 ON T1.Course_ID  =  T3.Course_ID WHERE T3.Course  =  "Math"
SELECT T2.Name ,  COUNT(*) FROM course_arrange AS T1 JOIN teacher AS T2 ON T1.Teacher_ID  =  T2.Teacher_ID GROUP BY T2.Name
SELECT T2.Name ,  COUNT(*) FROM course_arrange AS T1 JOIN teacher AS T2 ON T1.Teacher_ID  =  T2.Teacher_ID GROUP BY T2.Name
SELECT T2.Name FROM course_arrange AS T1 JOIN teacher AS T2 ON T1.Teacher_ID  =  T2.Teacher_ID GROUP BY T2.Name HAVING COUNT(*)  >=  2
SELECT T2.Name FROM course_arrange AS T1 JOIN teacher AS T2 ON T1.Teacher_ID  =  T2.Teacher_ID GROUP BY T2.Name HAVING COUNT(*)  >=  2
SELECT Name FROM teacher WHERE Teacher_ID NOT IN (SELECT Teacher_ID FROM course_arrange)
SELECT Name FROM teacher WHERE Teacher_ID NOT IN (SELECT Teacher_ID FROM course_arrange)
SELECT count(*) FROM visitor WHERE age  <  30
SELECT name FROM visitor WHERE Level_of_membership  >  4 ORDER BY Level_of_membership DESC
SELECT avg(age) FROM visitor WHERE Level_of_membership  >  4
SELECT name ,  level_of_membership FROM visitor WHERE level_of_membership  >  4 ORDER BY age DESC
SELECT Museum_ID ,  name FROM museum ORDER BY Num_of_Staff DESC LIMIT 1
SELECT avg(num_of_staff) FROM museum WHERE open_year  <  2009
SELECT open_year ,  num_of_staff FROM museum WHERE name  =  'Plaza Museum'
SELECT name FROM museum WHERE num_of_staff  >  (SELECT min(num_of_staff) FROM museum WHERE open_year  >  2010)
SELECT T1.id ,  T1.name ,  T1.age FROM visitor AS T1 JOIN visit AS T2 ON T1.id  =  T2.visitor_id GROUP BY T1.id HAVING count(*)  >  1
SELECT T1.id ,  T1.name ,  T1.level_of_membership FROM visitor AS T1 JOIN visit AS T2 ON T1.id  =  T2.visitor_id GROUP BY T1.id ORDER BY sum(T2.total_spent) DESC LIMIT 1
SELECT T2.id ,  T2.name FROM visit AS T1 JOIN museum AS T2 ON T1.museum_id  =  T2.museum_id GROUP BY T1.visitor_id ORDER BY count(*) DESC LIMIT 1
SELECT name FROM museum WHERE museum_id NOT IN (SELECT museum_id FROM visit)
SELECT T1.name ,  T1.age FROM visitor AS T1 JOIN visit AS T2 ON T1.id  =  T2.visitor_id GROUP BY T2.visitor_id ORDER BY sum(T2.num_of_ticket) DESC LIMIT 1
SELECT avg(Num_of_Ticket) ,  max(Num_of_Ticket) FROM visit
SELECT sum(T2.total_spent) FROM visitor AS T1 JOIN visit AS T2 ON T1.id  =  T2.visitor_id WHERE T1.level_of_membership  =  1
SELECT T2.name FROM visit AS T1 JOIN visitor AS T2 ON T1.visitor_id  =  T2.id JOIN museum AS T3 ON T1.museum_id  =  T3.museum_id WHERE T3.open_year  <  2009 INTERSECT SELECT T2.name FROM visit AS T1 JOIN visitor AS T2 ON T1.visitor_id  =  T2.id JOIN museum AS T3 ON T1.museum_id  =  T3.museum_id WHERE T3.open_year  >  2011
SELECT count(*) FROM visitor WHERE id NOT IN (SELECT visitor_id FROM visit WHERE museum_id IN (SELECT museum_id FROM museum WHERE open_year  >  2010))
SELECT count(*) FROM museum WHERE open_year  >  2013 OR open_year  <  2008
SELECT count(*) FROM players
SELECT count(*) FROM players
SELECT count(*) FROM MATCHES
SELECT count(*) FROM MATCHES
SELECT first_name ,  birth_date FROM players WHERE country_code  =  'USA'
SELECT first_name ,  birth_date FROM players WHERE country_code  =  'USA'
SELECT avg(loser_age) ,  avg(winner_age) FROM MATCHES
SELECT avg(loser_age) ,  avg(winner_age) FROM MATCHES
SELECT avg(winner_rank) FROM matches
SELECT avg(winner_rank) FROM matches
SELECT max(loser_rank) FROM matches
SELECT max(loser_rank) FROM matches
SELECT count(DISTINCT country_code) FROM players
SELECT count(DISTINCT country_code) FROM players
SELECT count(DISTINCT loser_name) FROM MATCHES
SELECT count(DISTINCT loser_name) FROM MATCHES
SELECT tourney_name FROM matches GROUP BY tourney_name HAVING count(*)  >  10
SELECT tourney_name FROM matches GROUP BY tourney_name HAVING count(*)  >  10
SELECT winner_name FROM matches WHERE YEAR  =  2013 INTERSECT SELECT winner_name FROM matches WHERE YEAR  =  2016
SELECT T1.winner_name FROM players AS T1 JOIN matches AS T2 ON T1.player_id  =  T2.winner_id WHERE T2.year  =  2013 INTERSECT SELECT T1.winner_name FROM players AS T1 JOIN matches AS T2 ON T1.player_id  =  T2.winner_id WHERE T2.year  =  2016
SELECT count(*) FROM matches WHERE YEAR  =  2013 OR YEAR  =  2016
SELECT count(*) FROM matches WHERE YEAR  =  2013 OR YEAR  =  2016
SELECT T1.country_code ,  T1.first_name FROM players AS T1 JOIN matches AS T2 ON T1.player_id  =  T2.winner_id WHERE tourney_name  =  'WTA Championships' INTERSECT SELECT T1.country_code ,  T1.first_name FROM players AS T1 JOIN matches AS T2 ON T1.player_id  =  T2.winner_id WHERE tourney_name  =  'Australian Open'
SELECT T1.first_name ,  T1.country_code FROM players AS T1 JOIN matches AS T2 ON T1.player_id  =  T2.winner_id WHERE tourney_name  =  'Australian Open' INTERSECT SELECT T1.first_name ,  T1.country_code FROM players AS T1 JOIN matches AS T2 ON T1.player_id  =  T2.winner_id WHERE tourney_name  =  'WTA Championships'
SELECT first_name ,  country_code FROM players ORDER BY birth_date LIMIT 1
SELECT first_name ,  country_code FROM players ORDER BY birth_date LIMIT 1
SELECT first_name ,  last_name FROM players ORDER BY birth_date
SELECT first_name ,  last_name FROM players ORDER BY birth_date
SELECT first_name ,  last_name FROM players WHERE hand  =  'L' ORDER BY birth_date
SELECT first_name ,  last_name FROM players WHERE hand  =  'L' ORDER BY birth_date
SELECT T1.first_name ,  T1.country_code FROM players AS T1 JOIN rankings AS T2 ON T1.player_id  =  T2.player_id GROUP BY T2.player_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.first_name ,  T1.country_code FROM players AS T1 JOIN rankings AS T2 ON T1.player_id  =  T2.player_id GROUP BY T2.player_id ORDER BY count(*) DESC LIMIT 1
SELECT YEAR FROM MATCHES GROUP BY YEAR ORDER BY COUNT(*) DESC LIMIT 1
SELECT YEAR FROM MATCHES GROUP BY YEAR ORDER BY COUNT(*) DESC LIMIT 1
SELECT T1.winner_name ,  T1.winner_rank_points FROM matches AS T1 JOIN (SELECT winner_id ,  COUNT(*) AS count FROM matches GROUP BY winner_id ORDER BY count DESC LIMIT 1) AS T2 ON T1.winner_id  =  T2.winner_id
SELECT T1.winner_name ,  T2.winner_rank_points FROM matches AS T1 JOIN players AS T2 ON T1.winner_id  =  T2.player_id GROUP BY T1.winner_name ORDER BY count(*) DESC LIMIT 1
SELECT T1.winner_name FROM players AS T2 JOIN matches AS T1 ON T2.player_id  =  T1.winner_id WHERE T1.tourney_name  =  "Australian Open" ORDER BY T1.winner_rank_points DESC LIMIT 1
SELECT T1.winner_name FROM players AS T1 JOIN matches AS T2 ON T1.player_id  =  T2.winner_id WHERE T2.tourney_name  =  "Australian Open" ORDER BY T2.winner_rank_points DESC LIMIT 1
SELECT T1.loser_name ,  T1.winner_name FROM matches AS T1 JOIN players AS T2 ON T1.loser_id  =  T2.player_id WHERE T1.minutes  =  (SELECT max(minutes) FROM matches)
SELECT winner_name ,  loser_name FROM MATCHES ORDER BY minutes DESC LIMIT 1
SELECT T1.first_name ,  avg(T2.ranking) FROM players AS T1 JOIN rankings AS T2 ON T1.player_id  =  T2.player_id GROUP BY T1.first_name
SELECT T1.first_name ,  avg(T2.ranking) FROM players AS T1 JOIN rankings AS T2 ON T1.player_id  =  T2.player_id GROUP BY T2.player_id
SELECT T1.first_name ,  T2.ranking_points ,  T1.player_id FROM players AS T1 JOIN rankings AS T2 ON T1.player_id  =  T2.player_id
SELECT T1.first_name ,  sum(T2.ranking_points) FROM players AS T1 JOIN rankings AS T2 ON T1.player_id  =  T2.player_id GROUP BY T2.player_id
SELECT country_code ,  count(*) FROM players GROUP BY country_code
SELECT country_code ,  count(*) FROM players GROUP BY country_code
SELECT country_code FROM players GROUP BY country_code ORDER BY count(*) DESC LIMIT 1
SELECT country_code FROM players GROUP BY country_code ORDER BY count(*) DESC LIMIT 1
SELECT country_code FROM players GROUP BY country_code HAVING count(*)  >  50
SELECT country_code FROM players GROUP BY country_code HAVING count(*)  >  50
SELECT ranking_date ,  count(DISTINCT tours) FROM rankings GROUP BY ranking_date
SELECT ranking_date ,  count(DISTINCT tours) FROM rankings GROUP BY ranking_date
SELECT count(*) ,  YEAR FROM MATCHES GROUP BY YEAR
SELECT count(*) ,  YEAR FROM MATCHES GROUP BY YEAR
SELECT winner_name ,  winner_rank FROM MATCHES ORDER BY winner_age LIMIT 3
SELECT winner_name ,  winner_rank FROM matches ORDER BY winner_age LIMIT 3
SELECT count(*) FROM players AS T1 JOIN matches AS T2 ON T1.player_id  =  T2.winner_id WHERE T2.tourney_name  =  'WTA Championships' AND T1.hand  =  'left'
SELECT count(*) FROM players AS T1 JOIN matches AS T2 ON T1.player_id  =  T2.winner_id WHERE T1.hand  =  'L' AND T2.tourney_level  =  'WTA'
SELECT T1.first_name ,  T1.country_code ,  T1.birth_date FROM players AS T1 JOIN matches AS T2 ON T1.player_id  =  T2.winner_id ORDER BY T2.winner_rank_points DESC LIMIT 1
SELECT T1.first_name ,  T1.country_code ,  T1.birth_date FROM players AS T1 JOIN matches AS T2 ON T1.player_id  =  T2.winner_id GROUP BY T2.winner_id ORDER BY sum(T2.winner_rank_points) DESC LIMIT 1
SELECT hand ,  count(*) FROM players GROUP BY hand
SELECT hand ,  count(*) FROM players GROUP BY hand
SELECT count(*) FROM ship WHERE disposition_of_ship  =  'Captured'
SELECT name ,  tonnage FROM ship ORDER BY name DESC
SELECT name ,  date ,  result FROM battle
SELECT max(killed) ,  min(killed) FROM death
SELECT avg(injured) FROM death
SELECT T1.note ,  T1.killed ,  T1.injured FROM death AS T1 JOIN ship AS T2 ON T1.caused_by_ship_id  =  T2.id WHERE T2.tonnage  =  "t"
SELECT name ,  result FROM battle WHERE bulgarian_commander != 'Boril'
SELECT DISTINCT T1.id ,  T1.name FROM battle AS T1 JOIN ship AS t2 ON T1.id  =  T2.lost_in_battle WHERE T2.ship_type  =  'Brig'
SELECT T1.id ,  T1.name FROM battle AS T1 JOIN ship AS T2 ON T1.id  =  T2.lost_in_battle JOIN death AS T3 ON T2.id  =  T3.caused_by_ship_id GROUP BY T1.id HAVING sum(T3.killed)  >  10
SELECT T1.id ,  T1.name FROM ship AS T1 JOIN death AS T2 ON T1.id  =  T2.caused_by_ship_id GROUP BY T2.caused_by_ship_id ORDER BY sum(T2.injured) DESC LIMIT 1
SELECT DISTINCT name FROM battle WHERE bulgarian_commander  =  'Kaloyan' AND latin_commander  =  'Baldwin I'
SELECT count(DISTINCT result) FROM battle
SELECT count(*) FROM battle WHERE battle.id NOT IN ( SELECT battle.id FROM battle JOIN ship ON battle.id  =  ship.lost_in_battle WHERE ship.tonnage  =  225 )
SELECT T3.name ,  T3.date FROM ship AS T1 JOIN battle AS T3 ON T1.lost_in_battle  =  T3.id JOIN ship AS T2 ON T2.lost_in_battle  =  T3.id WHERE T1.name  =  'Lettice' AND T2.name  =  'HMS Atalanta'
SELECT name ,  result ,  bulgarian_commander FROM battle WHERE battle.id NOT IN (SELECT ship.lost_in_battle FROM ship WHERE ship.location  =  'English Channel')
SELECT note FROM death WHERE note LIKE '%East%'
SELECT line_1 ,  line_2 FROM addresses
SELECT line_1 ,  line_2 FROM addresses
SELECT count(*) FROM courses
SELECT count(*) FROM courses
SELECT course_description FROM courses WHERE course_name  =  "math"
SELECT course_description FROM courses WHERE course_name  =  'Math'
SELECT zip_postcode FROM addresses WHERE city  =  "Port Chelsea"
SELECT zip_postcode FROM addresses WHERE line_1  =  "Port Chelsea"
SELECT T1.department_name ,  T2.department_id FROM departments AS T1 JOIN degree_programs AS T2 ON T1.department_id  =  T2.department_id GROUP BY T2.department_id ORDER BY count(*) DESC LIMIT 1
SELECT T2.department_name ,  T1.department_id FROM degree_programs AS T1 JOIN departments AS T2 ON T1.department_id  =  T2.department_id GROUP BY T1.department_id ORDER BY count(*) DESC LIMIT 1
SELECT count(DISTINCT department_id) FROM degree_programs
SELECT count(DISTINCT department_id) FROM degree_programs
SELECT count(DISTINCT degree_summary_name) FROM degree_programs
SELECT count(DISTINCT degree_summary_name) FROM degree_programs
SELECT count(*) FROM degree_programs AS T1 JOIN departments AS T2 ON T1.department_id  =  T2.department_id WHERE department_name  =  "Engineering"
SELECT count(*) FROM degree_programs AS T1 JOIN departments AS T2 ON T1.department_id  =  T2.department_id WHERE T2.department_name  =  "Engineering"
SELECT section_name ,  section_description FROM SECTIONS
SELECT section_name ,  section_description FROM SECTIONS
SELECT T1.course_name ,  T1.course_id FROM courses AS T1 JOIN sections AS T2 ON T1.course_id  =  T2.course_id GROUP BY T1.course_id HAVING count(*)  <=  2
SELECT course_name ,  course_id FROM courses WHERE course_id NOT IN (SELECT course_id FROM sections GROUP BY course_id HAVING count(*)  >=  2)
SELECT section_name FROM sections ORDER BY section_name DESC
SELECT section_name FROM sections ORDER BY section_name DESC
SELECT T1.semester_name ,  T1.semester_id FROM Semesters AS T1 JOIN Student_Enrolment AS T2 ON T1.semester_id  =  T2.semester_id GROUP BY T1.semester_id ORDER BY count(*) DESC LIMIT 1
SELECT T2.semester_name ,  T1.semester_id FROM Student_Enrolment AS T1 JOIN Semesters AS T2 ON T1.semester_id  =  T2.semester_id GROUP BY T1.semester_id ORDER BY count(*) DESC LIMIT 1
SELECT department_description FROM DEPARTMENTS WHERE department_name LIKE '%the computer%'
SELECT department_description FROM DEPARTMENTS WHERE department_name LIKE "%computer%"
SELECT T1.first_name ,  T1.middle_name ,  T1.last_name ,  T1.student_id FROM Students AS T1 JOIN Student_Enrolment AS T2 ON T1.student_id  =  T2.student_id WHERE T2.semester_id IN ( SELECT semester_id FROM Student_Enrolment GROUP BY semester_id HAVING count(*)  =  2 )
SELECT T1.first_name ,  T1.middle_name ,  T1.last_name ,  T1.student_id FROM Students AS T1 JOIN Student_Enrolment AS T2 ON T1.student_id  =  T2.student_id WHERE T2.student_id IN (SELECT T2.student_id FROM Students AS T1 JOIN Student_Enrolment AS T2 ON T1.student_id  =  T2.student_id WHERE T2.semester_id IN (SELECT T2.semester_id FROM Students AS T1 JOIN Student_Enrolment AS T2 ON T1.student_id  =  T2.student_id GROUP BY T2.semester_id HAVING COUNT(*)  =  2))
SELECT T2.first_name ,  T2.middle_name ,  T2.last_name FROM student_enrolment AS T1 JOIN students AS T2 ON T1.student_id  =  T2.student_id JOIN degree_programs AS T3 ON T1.degree_program_id  =  T3.degree_program_id WHERE T3.degree_summary_name  =  "Bachelor"
SELECT T3.first_name ,  T3.middle_name ,  T3.last_name FROM Student_Enrolment AS T1 JOIN Degree_Programs AS T2 ON T1.degree_program_id  =  T2.degree_program_id JOIN Students AS T3 ON T1.student_id  =  T3.student_id WHERE T2.degree_summary_name  =  "Bachelors"
SELECT T2.degree_summary_name FROM Student_Enrolment AS T1 JOIN Degree_Programs AS T2 ON T1.degree_program_id  =  T2.degree_program_id GROUP BY T1.degree_program_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.degree_summary_name FROM degree_programs AS T1 JOIN student_enrolment AS T2 ON T1.degree_program_id  =  T2.degree_program_id GROUP BY T1.degree_summary_name ORDER BY count(*) DESC LIMIT 1
SELECT T1.degree_summary_name ,  T1.degree_program_id FROM degree_programs AS T1 JOIN student_enrolment AS T2 ON T1.degree_program_id = T2.degree_program_id GROUP BY T1.degree_program_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.degree_summary_name ,  T1.degree_program_id FROM degree_programs AS T1 JOIN student_enrolment AS T2 ON T1.degree_program_id  =  T2.degree_program_id GROUP BY T1.degree_program_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.student_id ,  T2.first_name ,  T2.middle_name ,  T2.last_name ,  count(*) FROM Student_Enrolment AS T1 JOIN Students AS T2 ON T1.student_id  =  T2.student_id GROUP BY T1.student_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.first_name ,  T1.middle_name ,  T1.last_name ,  T1.student_id ,  count(*) FROM STUDENTS AS T1 JOIN student_enrolment AS T2 ON T1.student_id  =  T2.student_id GROUP BY T1.student_id ORDER BY count(*) DESC LIMIT 1
SELECT semester_name FROM semesters WHERE semester_id NOT IN (SELECT semester_id FROM student_enrolment)
SELECT semester_name FROM semesters WHERE semester_id NOT IN (SELECT semester_id FROM student_enrolment)
SELECT T2.course_name FROM Student_Enrolment_Courses AS T1 JOIN Courses AS T2 ON T1.course_id  =  T2.course_id
SELECT T1.course_name FROM courses AS T1 JOIN student_enrolment_courses AS T2 ON T1.course_id  =  T2.course_id GROUP BY T1.course_name HAVING COUNT(*)  >  0
SELECT T1.course_name FROM courses AS T1 JOIN student_enrolment_courses AS T2 ON T1.course_id  =  T2.course_id GROUP BY T1.course_name ORDER BY count(*) DESC LIMIT 1
SELECT T1.course_name FROM courses AS T1 JOIN student_enrolment_courses AS T2 ON T1.course_id  =  T2.course_id GROUP BY T1.course_name ORDER BY count(*) DESC LIMIT 1
SELECT last_name FROM students WHERE current_address_id IN (SELECT address_id FROM addresses WHERE state_province_county  =  'North Carolina') EXCEPT SELECT T1.last_name FROM students AS T1 JOIN student_enrolment AS T2 ON T1.student_id  =  T2.student_id
SELECT last_name FROM students WHERE current_address_id IN (SELECT address_id FROM addresses WHERE state_province_county  =  'North Carolina') EXCEPT SELECT T1.last_name FROM students AS T1 JOIN student_enrolment AS T2 ON T1.student_id  =  T2.student_id
SELECT T1.transcript_date ,  T1.transcript_id FROM Transcripts AS T1 JOIN Transcript_Contents AS T2 ON T1.transcript_id  =  T2.transcript_id GROUP BY T1.transcript_id HAVING count(*)  >=  2
SELECT T2.transcript_date ,  T1.transcript_id FROM Transcript_Contents AS T1 JOIN Transcripts AS T2 ON T1.transcript_id  =  T2.transcript_id GROUP BY T1.transcript_id HAVING count(*)  >=  2
SELECT cell_mobile_number FROM students WHERE first_name  =  "Timmothy" AND last_name  =  "Ward"
SELECT cell_mobile_number FROM STUDENTS WHERE first_name  =  "Timmothy" AND last_name  =  "Ward"
SELECT first_name ,  middle_name ,  last_name FROM Students ORDER BY date_first_registered LIMIT 1
SELECT first_name ,  middle_name ,  last_name FROM Students ORDER BY date_first_registered LIMIT 1
SELECT T1.first_name ,  T1.middle_name ,  T1.last_name FROM STUDENTS AS T1 JOIN student_enrolment AS T2 ON T1.student_id  =  T2.student_id ORDER BY T2.date_left LIMIT 1
SELECT T1.first_name ,  T1.middle_name , T1.last_name FROM Students AS T1 JOIN Student_Enrolment AS T2 ON T1.student_id  =  T2.student_id WHERE T2.date_left  =  (SELECT min(date_left) FROM Student_Enrolment)
SELECT first_name FROM students WHERE permanent_address_id != current_address_id
SELECT first_name FROM students WHERE permanent_address_id != current_address_id
SELECT T1.address_id ,  T1.line_1 ,  T1.line_2 ,  T1.line_3 FROM addresses AS T1 JOIN students AS T2 ON T1.address_id  =  T2.current_address_id GROUP BY T1.address_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.address_id ,  T1.line_1 ,  T1.line_2 FROM addresses AS T1 JOIN students AS T2 ON T1.address_id  =  T2.permanent_address_id GROUP BY T1.address_id ORDER BY count(*) DESC LIMIT 1
SELECT avg(transcript_date) FROM Transcripts
SELECT avg(transcript_date) FROM Transcripts
SELECT transcript_date ,  other_details FROM Transcripts ORDER BY transcript_date ASC LIMIT 1
SELECT other_details FROM Transcripts ORDER BY transcript_date ASC LIMIT 1
SELECT count(*) FROM TRANSCRIPTS
SELECT count(*) FROM TRANSCRIPTS
SELECT transcript_date FROM Transcripts ORDER BY transcript_date DESC LIMIT 1
SELECT transcript_date FROM Transcripts ORDER BY transcript_date DESC LIMIT 1
SELECT max(T2.student_course_id) ,  T1.student_course_id FROM Transcript_Contents AS T1 JOIN Student_Enrolment_Courses AS T2 ON T1.student_course_id  =  T2.student_course_id GROUP BY T1.student_course_id
SELECT max(T2.student_course_id) ,  T1.course_id FROM courses AS T1 JOIN student_enrolment_courses AS T2 ON T1.course_id  =  T2.course_id JOIN transcript_contents AS T3 ON T2.student_course_id  =  T3.student_course_id GROUP BY T1.course_id
SELECT T1.transcript_date ,  T1.transcript_id FROM Transcripts AS T1 JOIN Transcript_Contents AS T2 ON T1.transcript_id  =  T2.transcript_id GROUP BY T1.transcript_id ORDER BY count(*) ASC LIMIT 1
SELECT T1.transcript_date ,  T1.transcript_id FROM Transcripts AS T1 JOIN Transcript_Contents AS T2 ON T1.transcript_id  =  T2.transcript_id GROUP BY T1.transcript_id ORDER BY count(*) ASC LIMIT 1
SELECT T1.semester_name FROM semesters AS T1 JOIN student_enrolment AS T2 ON T1.semester_id  =  T2.semester_id WHERE T2.degree_program_id  =  1 INTERSECT SELECT T1.semester_name FROM semesters AS T1 JOIN student_enrolment AS T2 ON T1.semester_id  =  T2.semester_id WHERE T2.degree_program_id  =  2
SELECT T1.semester_id FROM Student_Enrolment AS T1 JOIN Degree_Programs AS T2 ON T1.degree_program_id  =  T2.degree_program_id WHERE T2.degree_summary_name  =  'Bachelors' INTERSECT SELECT T1.semester_id FROM Student_Enrolment AS T1 JOIN Degree_Programs AS T2 ON T1.degree_program_id  =  T2.degree_program_id WHERE T2.degree_summary_name  =  'Masters'
SELECT count(DISTINCT current_address_id) FROM students
SELECT DISTINCT T1.line_1 FROM addresses AS T1 JOIN students AS T2 ON T1.address_id  =  T2.permanent_address_id
SELECT student_id ,  other_student_details FROM students ORDER BY other_student_details DESC
SELECT other_student_details FROM students ORDER BY last_name DESC
SELECT section_description FROM SECTIONS WHERE section_name  =  "h"
SELECT section_description FROM SECTIONS WHERE section_name  =  "h"
SELECT first_name FROM students WHERE permanent_address_id IN (SELECT address_id FROM addresses WHERE country  =  'Haiti') OR cell_mobile_number  =  '09700166582'
SELECT first_name FROM students WHERE permanent_address_id IN (SELECT address_id FROM addresses WHERE country  =  'Haiti') OR cell_mobile_number  =  '09700166582'
SELECT title FROM cartoon ORDER BY title
SELECT title FROM cartoon ORDER BY title
SELECT title FROM cartoon WHERE directed_by  =  "Ben Jones"
SELECT title FROM cartoon WHERE directed_by  =  'Ben Jones'
SELECT count(*) FROM cartoon WHERE written_by  =  "Joseph Kuhr"
SELECT count(*) FROM cartoon WHERE written_by  =  "Joseph Kuhr"
SELECT title ,  directed_by FROM cartoon ORDER BY original_air_date
SELECT title ,  directed_by FROM cartoon ORDER BY original_air_date
SELECT title FROM cartoon WHERE directed_by  =  "Ben Jones" OR directed_by  =  "Brandon Vietti"
SELECT title FROM cartoon WHERE directed_by  =  'Ben Jones' OR directed_by  =  'Brandon Vietti'
SELECT country ,  count(*) FROM tv_channel GROUP BY country ORDER BY count(*) DESC LIMIT 1
SELECT country ,  count(*) FROM tv_channel GROUP BY country ORDER BY count(*) DESC LIMIT 1
SELECT count(DISTINCT series_name) ,  count(DISTINCT CONTENT) FROM TV_channel
SELECT count(DISTINCT series_name) ,  count(DISTINCT content) FROM TV_channel
SELECT content FROM TV_channel WHERE series_name  =  "Sky Radio"
SELECT content FROM TV_channel WHERE series_name  =  "Sky Radio"
SELECT Package_Option FROM TV_Channel WHERE series_name  =  "Sky Radio"
SELECT package_option FROM TV_channel WHERE series_name  =  "Sky Radio"
SELECT count(*) FROM TV_channel WHERE Language  =  'English'
SELECT count(*) FROM TV_channel WHERE Language  =  'English'
SELECT language ,  count(*) FROM TV_channel GROUP BY language ORDER BY count(*) ASC LIMIT 1
SELECT language ,  count(*) FROM tv_channel GROUP BY language ORDER BY count(*) ASC LIMIT 1
SELECT language ,  count(*) FROM TV_channel GROUP BY language
SELECT count(*) ,  language FROM TV_channel GROUP BY language
SELECT T1.series_name FROM tv_channel AS T1 JOIN cartoon AS T2 ON T1.id  =  T2.channel WHERE T2.title  =  'The Rise of the Blue Beetle!'
SELECT t1.series_name FROM tv_channel AS t1 JOIN cartoon AS t2 ON t1.id  =  t2.channel WHERE t2.title  =  'The Rise of the Blue Beetle'
SELECT T1.title FROM cartoon AS T1 JOIN tv_channel AS T2 ON T1.channel  =  T2.id WHERE T2.series_name  =  "Sky Radio"
SELECT title FROM cartoon AS T1 JOIN tv_channel AS T2 ON T1.channel  =  T2.id WHERE T2.series_name  =  "Sky Radio"
SELECT Episode FROM TV_series ORDER BY rating
SELECT Episode FROM TV_series ORDER BY Rating
SELECT episode ,  rating FROM tv_series ORDER BY rating DESC LIMIT 3
SELECT episode ,  rating FROM tv_series ORDER BY rating DESC LIMIT 3
SELECT min(share) ,  max(share) FROM TV_series
SELECT max(share) ,  min(share) FROM TV_series
SELECT air_date FROM tv_series WHERE Episode  =  "A Love of a Lifetime"
SELECT air_date FROM tv_series WHERE Episode  =  "A Love of a Lifetime"
SELECT weekly_rank FROM tv_series WHERE Episode  =  "A Love of a Lifetime"
SELECT weekly_rank FROM tv_series WHERE Episode  =  "A Love of a Lifetime"
SELECT T2.series_name FROM TV_series AS T1 JOIN TV_channel AS T2 ON T1.channel  =  T2.id WHERE T1.Episode  =  "A Love of a Lifetime"
SELECT series_name FROM tv_channel AS T1 JOIN tv_series AS T2 ON T1.id  =  T2.channel WHERE Episode  =  "A Love of a Lifetime"
SELECT T2.episode FROM TV_channel AS T1 JOIN TV_series AS T2 ON T1.id  =  T2.channel WHERE T1.series_name  =  "Sky Radio"
SELECT episode FROM tv_series AS T1 JOIN tv_channel AS T2 ON T1.channel  =  T2.id WHERE T2.series_name  =  "Sky Radio"
SELECT directed_by ,  count(*) FROM cartoon GROUP BY directed_by
SELECT directed_by ,  count(*) FROM cartoon GROUP BY directed_by
SELECT production_code ,  channel FROM cartoon ORDER BY original_air_date DESC LIMIT 1
SELECT production_code ,  channel FROM cartoon ORDER BY original_air_date DESC LIMIT 1
SELECT package_option ,  series_name FROM tv_channel WHERE hight_definition_tv  =  'Yes'
SELECT package_option ,  series_name FROM tv_channel WHERE hight_definition_tv  =  'Yes'
SELECT T2.country FROM cartoon AS T1 JOIN tv_channel AS T2 ON T1.channel  =  T2.id WHERE T1.written_by  =  'Todd Casey'
SELECT T2.country FROM cartoon AS T1 JOIN tv_channel AS T2 ON T1.channel  =  T2.id WHERE T1.written_by  =  'Todd Casey'
SELECT DISTINCT country FROM tv_channel EXCEPT (SELECT T1.country FROM tv_channel AS T1 JOIN cartoon AS T2 ON T1.id  =  T2.channel WHERE T2.written_by  =  'Todd Casey')
SELECT country FROM tv_channel EXCEPT SELECT T2.country FROM cartoon AS T1 JOIN tv_channel AS T2 ON T1.channel  =  T2.id WHERE T1.written_by  =  'Todd Casey'
SELECT T2.series_name ,  T2.country FROM Cartoon AS T1 JOIN TV_channel AS T2 ON T1.channel  =  T2.id WHERE T1.directed_by  =  'Ben Jones' INTERSECT SELECT T2.series_name ,  T2.country FROM Cartoon AS T1 JOIN TV_channel AS T2 ON T1.channel  =  T2.id WHERE T1.directed_by  =  'Michael Chang'
SELECT T2.series_name ,  T2.country FROM Cartoon AS T1 JOIN TV_channel AS T2 ON T1.channel  =  T2.id WHERE directed_by  =  'Ben Jones' INTERSECT SELECT T2.series_name ,  T2.country FROM Cartoon AS T1 JOIN TV_channel AS T2 ON T1.channel  =  T2.id WHERE directed_by  =  'Michael Chang'
SELECT pixel_aspect_ratio_PAR ,  country FROM tv_channel WHERE language != 'English'
SELECT pixel_aspect_ratio_PAR ,  country FROM tv_channel WHERE Language != 'English'
SELECT id FROM tv_channel GROUP BY country HAVING count(*)  >  2
SELECT id FROM tv_channel GROUP BY id HAVING count(*)  >  2
SELECT id FROM tv_channel EXCEPT SELECT channel FROM cartoon WHERE directed_by  =  'Ben Jones'
SELECT id FROM tv_channel EXCEPT SELECT channel FROM cartoon WHERE directed_by  =  'Ben Jones'
SELECT package_option FROM tv_channel EXCEPT SELECT T2.package_option FROM cartoon AS T1 JOIN tv_channel AS T2 ON T1.channel  =  T2.id WHERE directed_by  =  'Ben Jones'
SELECT package_option FROM tv_channel EXCEPT SELECT T2.package_option FROM tv_channel AS T1 JOIN cartoon AS T2 ON T1.id  =  T2.channel WHERE directed_by  =  'Ben Jones'
SELECT count(*) FROM poker_player
SELECT count(*) FROM poker_player
SELECT Earnings FROM poker_player ORDER BY Earnings DESC
SELECT Earnings FROM poker_player ORDER BY Earnings DESC
SELECT Final_Table_Made ,  Best_Finish FROM poker_player
SELECT Final_Table_Made ,  Best_Finish FROM poker_player
SELECT avg(Earnings) FROM poker_player
SELECT avg(Earnings) FROM poker_player
SELECT Money_Rank FROM poker_player ORDER BY Earnings DESC LIMIT 1
SELECT Money_Rank FROM poker_player ORDER BY Earnings DESC LIMIT 1
SELECT max(Final_Table_Made) FROM poker_player WHERE Earnings  <  200000
SELECT max(Final_Table_Made) FROM poker_player WHERE Earnings  <  200000
SELECT T2.Name FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID  =  T2.People_ID
SELECT T2.Name FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID  =  T2.People_ID
SELECT T1.Name FROM people AS T1 JOIN poker_player AS T2 ON T1.People_ID  =  T2.People_ID WHERE T2.Earnings  >  300000
SELECT T1.Name FROM people AS T1 JOIN poker_player AS T2 ON T1.People_ID  =  T2.People_ID WHERE T2.Earnings  >  300000
SELECT T2.Name FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID  =  T2.People_ID ORDER BY T1.Final_Table_Made ASC
SELECT T2.Name FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID  =  T2.People_ID ORDER BY T1.Final_Table_Made ASC
SELECT T1.Birth_Date FROM people AS T1 JOIN poker_player AS T2 ON T1.People_ID  =  T2.People_ID ORDER BY T2.Earnings ASC LIMIT 1
SELECT T2.Birth_Date FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID  =  T2.People_ID ORDER BY T1.Earnings ASC LIMIT 1
SELECT Money_Rank FROM poker_player ORDER BY Earnings DESC LIMIT 1
SELECT Money_Rank FROM poker_player ORDER BY Earnings DESC LIMIT 1 INTERSECT SELECT T1.Money_Rank FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID  =  T2.People_ID ORDER BY T2.Height DESC LIMIT 1
SELECT avg(T1.Earnings) FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID  =  T2.People_ID WHERE T2.Height  >  200
SELECT avg(T1.Earnings) FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID  =  T2.People_ID WHERE T2.Height  >  200
SELECT T2.Name FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID  =  T2.People_ID ORDER BY T1.Earnings DESC
SELECT T2.Name FROM poker_player AS T1 JOIN people AS T2 ON T1.People_ID  =  T2.People_ID ORDER BY T1.Earnings DESC
SELECT Nationality ,  COUNT(*) FROM people GROUP BY Nationality
SELECT Nationality ,  COUNT(*) FROM people GROUP BY Nationality
SELECT Nationality FROM people GROUP BY Nationality ORDER BY COUNT(*) DESC LIMIT 1
SELECT Nationality FROM people GROUP BY Nationality ORDER BY COUNT(*) DESC LIMIT 1
SELECT Nationality FROM people GROUP BY Nationality HAVING COUNT(*)  >=  2
SELECT Nationality FROM people GROUP BY Nationality HAVING COUNT(*)  >=  2
SELECT Name ,  Birth_Date FROM people ORDER BY Name ASC
SELECT Name ,  Birth_Date FROM people ORDER BY Name ASC
SELECT Name FROM people WHERE Nationality != "Russia"
SELECT Name FROM people WHERE Nationality != "Russia"
SELECT Name FROM people WHERE People_ID NOT IN (SELECT People_ID FROM poker_player)
SELECT Name FROM people WHERE People_ID NOT IN (SELECT People_ID FROM poker_player)
SELECT count(DISTINCT Nationality) FROM people
SELECT count(DISTINCT Nationality) FROM people
SELECT count(DISTINCT state) FROM area_code_state
SELECT contestant_number ,  contestant_name FROM contestants ORDER BY contestant_name DESC
SELECT vote_id ,  phone_number ,  state FROM votes
SELECT max(area_code) ,  min(area_code) FROM AREA_CODE_STATE
SELECT max(created) FROM votes WHERE state  =  "CA"
SELECT contestant_name FROM contestants WHERE contestant_name != 'Jessie Alloway'
SELECT DISTINCT state ,  created FROM votes
SELECT T1.contestant_number ,  T2.contestant_name FROM votes AS T1 JOIN contestants AS T2 ON T1.contestant_number  =  T2.contestant_number GROUP BY T1.contestant_number HAVING count(*)  >=  2
SELECT T1.contestant_number ,  T2.contestant_name FROM votes AS T1 JOIN contestants AS T2 ON T1.contestant_number  =  T2.contestant_number GROUP BY T1.contestant_number ORDER BY count(*) LIMIT 1
SELECT count(*) FROM votes WHERE state  =  'NY' OR state  =  'CA'
SELECT count(*) FROM contestants WHERE contestant_number NOT IN (SELECT contestant_number FROM votes)
SELECT T1.area_code FROM area_code_state AS T1 JOIN votes AS T2 ON T1.state  =  T2.state GROUP BY T1.area_code ORDER BY count(*) DESC LIMIT 1
SELECT T1.created ,  T1.state ,  T1.phone_number FROM votes AS T1 JOIN contestants AS T2 ON T1.contestant_number  =  T2.contestant_number WHERE T2.contestant_name  =  "Tabatha Gehling"
SELECT T1.area_code FROM AREA_CODE_STATE AS T1 JOIN votes AS t2 ON t1.state  =  t2.state WHERE t2.contestant_number  =  "Tabatha Gehling" INTERSECT SELECT T1.area_code FROM AREA_CODE_STATE AS T1 JOIN votes AS t2 ON t1.state  =  t2.state WHERE t2.contestant_number  =  "Kelly Clauss"
SELECT contestant_name FROM contestants WHERE contestant_name LIKE '%Al%'
SELECT name FROM country WHERE indepyear  >  1950
SELECT name FROM country WHERE indepyear  >  1950
SELECT count(*) FROM country WHERE GovernmentForm  =  "Republic"
SELECT count(*) FROM country WHERE GovernmentForm  =  "Republic"
SELECT sum(SurfaceArea) FROM country WHERE Region  =  "Caribbean"
SELECT sum(SurfaceArea) FROM country WHERE region  =  "Caribbean";
SELECT Continent FROM country WHERE Name  =  "Anguilla"
SELECT Continent FROM country WHERE Name  =  "Anguilla"
SELECT Region FROM country WHERE Name  =  "Afghanistan"
SELECT Region FROM country WHERE Name  =  "Afghanistan"
SELECT Language FROM countrylanguage WHERE CountryCode  =  "AW" ORDER BY Percentage DESC LIMIT 1
SELECT countrylanguage.language FROM countrylanguage WHERE countrycode  =  "ABW" AND percentage  =  ( SELECT MAX ( percentage ) FROM countrylanguage WHERE countrycode  =  "ABW" );
SELECT Population ,  LifeExpectancy FROM country WHERE Name  =  "Brazil"
SELECT Population ,  LifeExpectancy FROM country WHERE Name  =  "Brazil"
SELECT Region ,  Population FROM country WHERE Name  =  "Angola"
SELECT Region ,  Population FROM country WHERE Name  =  "Angola"
SELECT avg(LifeExpectancy) FROM country WHERE Region  =  "Central Africa"
SELECT LifeExpectancy FROM country WHERE Continent  =  "Central Africa"
SELECT Name FROM country WHERE Continent  =  "Asia" AND LifeExpectancy  =  (SELECT min(LifeExpectancy) FROM country WHERE Continent  =  "Asia")
SELECT Name FROM country WHERE Continent  =  "Asia" ORDER BY LifeExpectancy LIMIT 1
SELECT sum(population) ,  max(GNP) FROM country WHERE continent  =  'Asia'
SELECT max(GNP) ,  population FROM country WHERE continent  =  'Asia' GROUP BY continent
SELECT avg(LifeExpectancy) FROM country WHERE Continent  =  'Africa' AND GovernmentForm  =  'Republic'
SELECT avg(LifeExpectancy) FROM country WHERE Continent  =  "Africa" AND GovernmentForm  =  "Republic"
SELECT sum(SurfaceArea) FROM country WHERE continent  =  "Asia" UNION SELECT sum(SurfaceArea) FROM country WHERE continent  =  "Europe"
SELECT sum(SurfaceArea) FROM country WHERE Continent  =  'Asia' OR Continent  =  'Europe'
SELECT SUM (Population) FROM city WHERE District  =  "Gelderland"
SELECT sum(Population) FROM city WHERE District  =  "Gelderland"
SELECT avg(GNP) ,  sum(Population) FROM country WHERE GovernmentForm  =  "US territory"
SELECT avg(GNP) ,  sum(Population) FROM country WHERE GovernmentForm  =  "Territory of the United States"
SELECT count(DISTINCT language) FROM countrylanguage
SELECT count(DISTINCT language) FROM countrylanguage
SELECT count(DISTINCT GovernmentForm) FROM country WHERE Continent  =  "Africa"
SELECT COUNT (DISTINCT GovernmentForm) FROM country WHERE Continent  =  "Africa"
SELECT sum(T2.percentage) FROM countrylanguage AS T1 JOIN country AS T2 ON T1.countrycode  =  T2.code WHERE T2.name  =  'Aruba'
SELECT count(*) FROM countrylanguage WHERE countrycode  =  "AW"
SELECT count(*) FROM countrylanguage WHERE countrycode  =  "AFG" AND isofficial  =  '1'
SELECT count(*) FROM countrylanguage WHERE countrycode  =  "AFG" AND isofficial  =  "1"
SELECT T1.name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode GROUP BY T2.countrycode ORDER BY count(*) DESC LIMIT 1
SELECT T1.name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode GROUP BY T2.countrycode ORDER BY count(*) DESC LIMIT 1
SELECT T1.Continent FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode GROUP BY T1.Continent ORDER BY COUNT(*) DESC LIMIT 1
SELECT T1.Continent FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode GROUP BY T1.Continent ORDER BY COUNT(*) DESC LIMIT 1
SELECT count(*) FROM countrylanguage WHERE language  =  'English' AND countrycode IN (SELECT countrycode FROM countrylanguage WHERE language  =  'Dutch')
SELECT count(*) FROM countrylanguage WHERE language  =  "English" AND language  =  "Dutch"
SELECT T1.name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode WHERE T2.language  =  'English' INTERSECT SELECT T1.name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode WHERE T2.language  =  'French'
SELECT T1.name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode WHERE T2.language  =  'English' INTERSECT SELECT T1.name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode WHERE T2.language  =  'French'
SELECT T1.name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode WHERE T2.language  =  'English' INTERSECT SELECT T1.name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode WHERE T2.language  =  'French'
SELECT T1.name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode WHERE T2.language  =  'English' INTERSECT SELECT T1.name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode WHERE T2.language  =  'French'
SELECT DISTINCT T1.continent FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode WHERE T2.language  =  'Chinese'
SELECT count(*) FROM countrylanguage WHERE Language  =  "Chinese"
SELECT T1.Region FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T2.Language  =  "English" OR T2.Language  =  "Dutch" GROUP BY T1.Region
SELECT T2.region FROM countrylanguage AS T1 JOIN country AS T2 ON T1.countrycode  =  T2.code WHERE T1.language  =  "Dutch" OR T1.language  =  "English" GROUP BY T2.region
SELECT T1.name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode WHERE T2.language  =  'English' OR T2.language  =  'Dutch' GROUP BY T2.countrycode HAVING count(*)  >=  2
SELECT T1.name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode WHERE T2.language  =  'English' OR T2.language  =  'Dutch'
SELECT t2.language FROM countrylanguage AS t2 JOIN country AS t1 ON t2.countrycode  =  t1.code WHERE t1.continent  =  "Asia" GROUP BY t2.language ORDER BY COUNT(*) DESC LIMIT 1
SELECT t1.language FROM countrylanguage AS t1 JOIN country AS t2 ON t1.countrycode  =  t2.code WHERE t2.continent  =  "Asia" GROUP BY t1.language ORDER BY COUNT(*) DESC LIMIT 1
SELECT Language FROM countrylanguage WHERE Percentage  =  100 AND CountryCode IN (SELECT CountryCode FROM country WHERE GovernmentForm  =  "Republic") GROUP BY Language HAVING COUNT(*)  =  1
SELECT Language FROM countrylanguage WHERE Percentage  =  100 AND CountryCode IN (SELECT CountryCode FROM country WHERE GovernmentForm  =  "Republic") GROUP BY Language HAVING COUNT(*)  =  1
SELECT t1.name FROM city AS t1 JOIN countrylanguage AS t2 ON t1.countrycode  =  t2.countrycode WHERE t2.language  =  "English" AND t2.percentage  =  (SELECT MAX(percentage) FROM countrylanguage WHERE language  =  "English")
SELECT t1.name FROM city AS t1 JOIN countrylanguage AS t2 ON t1.countrycode  =  t2.countrycode WHERE t2.language  =  'English' ORDER BY t1.population DESC LIMIT 1
SELECT name ,  population ,  lifeexpectancy FROM country WHERE continent  =  'Asia' AND surfacearea  =  (SELECT MAX(surfacearea) FROM country WHERE continent  =  'Asia')
SELECT Name ,  Population ,  LifeExpectancy FROM country WHERE Continent  =  "Asia" AND Population  =  (SELECT MAX(Population) FROM country WHERE Continent  =  "Asia")
SELECT avg(LifeExpectancy) FROM country WHERE Code NOT IN (SELECT CountryCode FROM countrylanguage WHERE IsOfficial  =  "T" AND Language  =  "English")
SELECT avg(LifeExpectancy) FROM country WHERE Code NOT IN (SELECT CountryCode FROM countrylanguage WHERE Language  =  "English")
SELECT sum(t1.population) FROM country AS t1 JOIN countrylanguage AS t2 ON t1.code  =  t2.countrycode WHERE t2.language  =  "English"
SELECT sum(t1.population) FROM country AS t1 LEFT JOIN countrylanguage AS t2 ON t1.code  =  t2.countrycode WHERE t2.language  =  'English' GROUP BY t2.countrycode HAVING count(*)  =  0
SELECT T2.Language FROM countrylanguage AS T1 JOIN country AS T2 ON T1.CountryCode  =  T2.Code WHERE T2.HeadOfState  =  "Beatrix"
SELECT T2.language FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode WHERE T1.headofstate  =  'Beatrix' AND T2.isofficial  =  '1'
SELECT sum(T1.percentage) FROM countrylanguage AS T1 JOIN country AS T2 ON T1.countrycode  =  T2.code WHERE T2.indepyear  <  1930 AND T1.isofficial  =  'yes'
SELECT count(DISTINCT t1.language) FROM countrylanguage AS t1 JOIN country AS t2 ON t1.countrycode  =  t2.code WHERE t2.indepyear  <  1930
SELECT name FROM country WHERE surfacearea  >  (SELECT max(surfacearea) FROM country WHERE continent  =  'Europe')
SELECT Name FROM country WHERE SurfaceArea  >  (SELECT max(SurfaceArea) FROM country WHERE Continent  =  "Europe")
SELECT name FROM country WHERE population  <  (SELECT min(population) FROM country WHERE continent  =  'Asia') AND continent  =  'Africa'
SELECT name FROM country WHERE population  <  (SELECT min(population) FROM country WHERE continent  =  'Asia') AND continent  =  'Africa'
SELECT name FROM country WHERE population  >  (SELECT max(population) FROM country WHERE continent  =  'Africa') AND continent  =  'Asia'
SELECT Name FROM country WHERE Continent  =  "Asia" AND Population  >  (SELECT max(Population) FROM country WHERE Continent  =  "Africa")
SELECT CountryCode FROM countrylanguage WHERE Language  =  "English"
SELECT CountryCode FROM countrylanguage WHERE Language != "English"
SELECT CountryCode FROM countrylanguage WHERE Language != "English"
SELECT CountryCode FROM countrylanguage WHERE Language != "English"
SELECT code FROM country WHERE governmentform != 'Republic' AND code NOT IN (SELECT countrycode FROM countrylanguage WHERE language  =  'English')
SELECT code FROM country WHERE governmentform != 'Republic' AND code NOT IN (SELECT countrycode FROM countrylanguage WHERE language  =  'English')
SELECT T1.Name FROM countrylanguage AS T2 JOIN city AS T1 ON T1.CountryCode  =  T2.CountryCode WHERE T2.Language  =  "English" AND T2.Percentage  >  50 JOIN country AS T3 ON T3.Code  =  T2.CountryCode WHERE T3.Continent  =  "Europe"
SELECT T2.name FROM countrylanguage AS T1 JOIN city AS T2 ON T1.countrycode  =  T2.countrycode WHERE T1.language  =  "English" AND T1.percentage  >  50 AND T1.CountryCode IN (SELECT CountryCode FROM country WHERE continent  =  "Europe")
SELECT T2.name FROM countrylanguage AS T1 JOIN city AS T2 ON T1.countrycode  =  T2.countrycode JOIN country AS T3 ON T3.code  =  T2.countrycode WHERE T1.language  =  'Chinese' AND T3.continent  =  'Asia'
SELECT DISTINCT T2.name FROM countrylanguage AS T1 JOIN city AS T2 ON T1.countrycode  =  T2.countrycode WHERE T1.language  =  "Chinese" AND T1.percentage  >  50 JOIN country AS T3 ON T2.countrycode  =  T3.code WHERE T3.continent  =  "Asia"
SELECT name ,  indepyear ,  surfacearea FROM country ORDER BY population LIMIT 1
SELECT name ,  indepyear ,  surfacearea FROM country ORDER BY population LIMIT 1
SELECT Population ,  name ,  HeadOfState FROM country WHERE surfacearea  =  ( SELECT MAX ( surfacearea ) FROM country )
SELECT name ,  population ,  headofstate FROM country WHERE surfacearea  =  ( SELECT MAX ( surfacearea ) FROM country )
SELECT T1.name ,  COUNT(*) FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode GROUP BY T1.name HAVING COUNT(*)  >=  3
SELECT T1.name ,  count(*) FROM country AS T1 JOIN countrylanguage AS T2 ON T1.code  =  T2.countrycode GROUP BY T1.name HAVING count(*)  >  2
SELECT District ,  COUNT(*) FROM city WHERE Population  >  (SELECT avg(Population) FROM city) GROUP BY District
SELECT District ,  COUNT(*) FROM city WHERE Population  >  (SELECT avg(Population) FROM city) GROUP BY District
SELECT GovernmentForm ,  SUM(Population) FROM country WHERE LifeExpectancy  >  72 GROUP BY GovernmentForm
SELECT GovernmentForm ,  SUM(Population) FROM country WHERE LifeExpectancy  >  72 GROUP BY GovernmentForm
SELECT avg(LifeExpectancy) ,  sum(Population) ,  Continent FROM country WHERE LifeExpectancy  <  72 GROUP BY Continent
SELECT Continent ,  avg(LifeExpectancy) ,  sum(Population) FROM country GROUP BY Continent HAVING avg(LifeExpectancy)  <  72
SELECT name ,  surfacearea FROM country ORDER BY surfacearea DESC LIMIT 5
SELECT name ,  surfacearea FROM country ORDER BY surfacearea DESC LIMIT 5
SELECT Name FROM country ORDER BY Population DESC LIMIT 3
SELECT Name FROM country ORDER BY Population DESC LIMIT 3
SELECT Name FROM country ORDER BY Population ASC LIMIT 3
SELECT Name FROM country ORDER BY Population ASC LIMIT 3
SELECT count(*) FROM country WHERE continent  =  'Asia'
SELECT count(*) FROM country WHERE continent  =  "Asia"
SELECT name FROM country WHERE population  >  80000 AND continent  =  'Europe'
SELECT name FROM country WHERE population  =  80000 AND continent  =  'Europe'
SELECT sum(Population) ,  avg(SurfaceArea) FROM country WHERE Continent  =  "North America" AND SurfaceArea  >  3000
SELECT sum(Population) ,  avg(SurfaceArea) FROM country WHERE Continent  =  "North America" AND SurfaceArea  >  3000
SELECT Name FROM city WHERE Population BETWEEN 160000 AND 900000
SELECT Name FROM city WHERE Population BETWEEN 160000 AND 900000
SELECT Language FROM countrylanguage GROUP BY Language ORDER BY COUNT(*) DESC LIMIT 1
SELECT Language FROM countrylanguage GROUP BY Language ORDER BY COUNT(*) DESC LIMIT 1
SELECT t1.language FROM countrylanguage AS t1 JOIN ( SELECT countrycode ,  max(percentage) FROM countrylanguage GROUP BY countrycode ) AS t2 ON t1.countrycode  =  t2.countrycode WHERE t1.percentage  =  t2.maxpercentage
SELECT CountryCode ,  Language FROM countrylanguage ORDER BY Percentage DESC LIMIT 1
SELECT count(*) FROM countrylanguage WHERE language  =  "Spanish" AND percentage  =  ( SELECT percentage FROM countrylanguage WHERE language  =  "Spanish" ORDER BY percentage DESC LIMIT 1 )
SELECT count(*) FROM countrylanguage WHERE language  =  "Spanish" AND percentage  >  50
SELECT CountryCode FROM countrylanguage WHERE Language  =  "Spanish" AND Percentage  =  (SELECT MAX(Percentage) FROM countrylanguage WHERE Language  =  "Spanish")
SELECT CountryCode FROM countrylanguage WHERE Language  =  "Spanish" AND Percentage  >  50
SELECT count(*) FROM conductor
SELECT count(*) FROM conductor
SELECT Name FROM conductor ORDER BY Age ASC
SELECT Name FROM conductor ORDER BY Age
SELECT name FROM conductor WHERE nationality != 'USA'
SELECT name FROM conductor WHERE nationality != 'USA'
SELECT record_company FROM orchestra ORDER BY YEAR_of_Founded DESC
SELECT record_company FROM orchestra ORDER BY YEAR_of_Founded DESC
SELECT avg(attendance) FROM show
SELECT avg(attendance) FROM show
SELECT max(share) ,  min(share) FROM performance WHERE TYPE != "Live final"
SELECT max(share) ,  min(share) FROM performance WHERE TYPE != "Live final"
SELECT count(DISTINCT nationality) FROM conductor
SELECT count(DISTINCT nationality) FROM conductor
SELECT Name FROM conductor ORDER BY Year_of_Work DESC
SELECT Name FROM conductor ORDER BY Year_of_Work DESC
SELECT name FROM conductor ORDER BY year_of_work DESC LIMIT 1
SELECT name FROM conductor ORDER BY year_of_work DESC LIMIT 1
SELECT T2.name ,  T1.orchestra FROM orchestra AS T1 JOIN conductor AS T2 ON T1.Conductor_ID  =  T2.Conductor_ID
SELECT T1.name ,  T2.orchestra FROM conductor AS T1 JOIN orchestra AS T2 ON T1.Conductor_ID  =  T2.Conductor_ID
SELECT T2.name FROM orchestra AS T1 JOIN conductor AS T2 ON T1.Conductor_ID  =  T2.Conductor_ID GROUP BY T2.Conductor_ID HAVING COUNT(*)  >  1
SELECT T2.name FROM orchestra AS T1 JOIN conductor AS T2 ON T1.Conductor_ID  =  T2.Conductor_ID GROUP BY T2.Conductor_ID HAVING count(*)  >  1
SELECT T2.name FROM orchestra AS T1 JOIN conductor AS T2 ON T1.Conductor_ID  =  T2.Conductor_ID GROUP BY T2.Conductor_ID ORDER BY count(*) DESC LIMIT 1
SELECT T2.name FROM orchestra AS T1 JOIN conductor AS T2 ON T1.Conductor_ID  =  T2.Conductor_ID GROUP BY T2.Conductor_ID ORDER BY count(*) DESC LIMIT 1
SELECT T2.name FROM orchestra AS T1 JOIN conductor AS T2 ON T1.Conductor_ID  =  T2.Conductor_ID WHERE T1.year_of_founded  >  2008
SELECT T2.name FROM orchestra AS T1 JOIN conductor AS T2 ON T1.Conductor_ID  =  T2.Conductor_ID WHERE T1.year_of_founded  >  2008
SELECT record_company ,  count(*) FROM orchestra GROUP BY record_company
SELECT record_company ,  count(*) FROM orchestra GROUP BY record_company
SELECT Major_Record_Format FROM orchestra GROUP BY Major_Record_Format ORDER BY COUNT(*) ASC
SELECT major_record_format FROM orchestra GROUP BY major_record_format ORDER BY count(*) DESC
SELECT record_company FROM orchestra GROUP BY record_company ORDER BY count(*) DESC LIMIT 1
SELECT record_company FROM orchestra GROUP BY record_company ORDER BY count(*) DESC LIMIT 1
SELECT orchestra FROM orchestra WHERE orchestra_id NOT IN (SELECT orchestra_id FROM performance)
SELECT orchestra FROM orchestra WHERE orchestra_id NOT IN (SELECT orchestra_id FROM performance)
SELECT record_company FROM orchestra WHERE YEAR_of_Founded  <  2003 INTERSECT SELECT record_company FROM orchestra WHERE YEAR_of_Founded  >  2003
SELECT record_company FROM orchestra WHERE YEAR_of_Founded  <  2003 INTERSECT SELECT record_company FROM orchestra WHERE YEAR_of_Founded  >  2003
SELECT count(*) FROM orchestra WHERE Major_Record_Format  =  "CD" OR Major_Record_Format  =  "DVD"
SELECT count(*) FROM orchestra WHERE Major_Record_Format  =  "CD" OR Major_Record_Format  =  "DVD"
SELECT T1.Year_of_Founded FROM ORCHESTRAL T1 JOIN PERFORMANCE T2 ON T1.Orchestra_ID  =  T2.Orchestra_ID GROUP BY T1.Year_of_Founded HAVING COUNT(*)  >  1
SELECT T1.Year_of_Founded FROM orchestra AS T1 JOIN performance AS T2 ON T1.Orchestra_ID  =  T2.Orchestra_ID GROUP BY T1.Orchestra_ID HAVING COUNT(*)  >  1
SELECT count(*) FROM highschooler
SELECT count(*) FROM highschooler
SELECT name ,  grade FROM Highschooler
SELECT name ,  grade FROM Highschooler
SELECT DISTINCT grade FROM highschooler
SELECT grade FROM Highschooler
SELECT grade FROM highschooler WHERE name  =  "Kyle"
SELECT grade FROM highschooler WHERE name  =  "Kyle"
SELECT name FROM highschooler WHERE grade  =  10
SELECT name FROM highschooler WHERE grade  =  10
SELECT id FROM highschooler WHERE name  =  "Kyle"
SELECT id FROM highschooler WHERE name  =  'Kyle'
SELECT count(*) FROM highschooler WHERE grade  =  9 OR grade  =  10
SELECT count(*) FROM highschooler WHERE grade  =  9 OR grade  =  10
SELECT count(*) ,  grade FROM highschooler GROUP BY grade
SELECT count(*) ,  grade FROM Highschooler GROUP BY grade
SELECT grade FROM highschooler GROUP BY grade ORDER BY count(*) DESC LIMIT 1
SELECT grade FROM highschooler GROUP BY grade ORDER BY count(*) DESC LIMIT 1
SELECT grade FROM highschooler GROUP BY grade HAVING count(*)  >=  4
SELECT grade FROM highschooler GROUP BY grade HAVING count(*)  >=  4
SELECT student_id ,  count(*) FROM Friend GROUP BY student_id
SELECT count(*) ,  student_id FROM Friend GROUP BY student_id
SELECT T1.name ,  count(*) FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.student_id GROUP BY T1.name
SELECT T1.name ,  count(*) FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.friend_id GROUP BY T1.name
SELECT T1.name FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.friend_id GROUP BY T2.student_id ORDER BY count(*) DESC LIMIT 1
SELECT t1.name FROM highschooler AS t1 JOIN friend AS t2 ON t1.id  =  t2.friend_id GROUP BY t2.student_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.name FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.friend_id GROUP BY T2.student_id HAVING count(*)  >=  3
SELECT T1.name FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.friend_id GROUP BY T2.student_id HAVING count(*)  >=  3
SELECT T1.name FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.friend_id WHERE T2.student_id IN (SELECT T2.student_id FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.friend_id WHERE T1.name  =  'Kyle')
SELECT T1.name FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.friend_id WHERE T2.student_id  =  (SELECT T1.id FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.student_id WHERE T2.friend_id  =  (SELECT T1.id FROM highschooler AS T1 WHERE T1.name  =  'Kyle'))
SELECT count(*) FROM Friend AS T1 JOIN highschooler AS T2 ON T1.friend_id  =  T2.id WHERE T2.name  =  'Kyle'
SELECT count(*) FROM Friend AS T1 JOIN Highschooler AS T2 ON T1.friend_id  =  T2.ID WHERE T2.name  =  'Kyle'
SELECT id FROM highschooler EXCEPT SELECT student_id FROM Friend
SELECT id FROM highschooler EXCEPT SELECT student_id FROM Friend
SELECT name FROM highschooler WHERE id NOT IN (SELECT student_id FROM Friend)
SELECT name FROM highschooler WHERE id NOT IN (SELECT student_id FROM Friend)
SELECT student_id FROM Friend INTERSECT SELECT student_id FROM Likes
SELECT student_id FROM Friend INTERSECT SELECT student_id FROM Likes
SELECT T1.name FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.student_id INTERSECT SELECT T1.name FROM highschooler AS T1 JOIN likes AS T2 ON T1.id  =  T2.student_id
SELECT T1.name FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.student_id INTERSECT SELECT T1.name FROM highschooler AS T1 JOIN likes AS T2 ON T1.id  =  T2.student_id
SELECT student_id ,  count(*) FROM Likes GROUP BY student_id
SELECT student_id ,  count(*) FROM Likes GROUP BY student_id
SELECT count(*) ,  T1.name FROM highschooler AS T1 JOIN likes AS T2 ON T1.id  =  T2.student_id GROUP BY T1.name
SELECT T1.name ,  count(*) FROM highschooler AS T1 JOIN likes AS T2 ON T1.id  =  T2.student_id GROUP BY T2.student_id
SELECT T2.name FROM Likes AS T1 JOIN highschooler AS T2 ON T1.liked_id  =  T2.id GROUP BY T1.liked_id ORDER BY count(*) DESC LIMIT 1
SELECT T2.name FROM Likes AS T1 JOIN highschooler AS T2 ON T1.liked_id  =  T2.id GROUP BY T1.liked_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.name FROM highschooler AS T1 JOIN likes AS T2 ON T1.id  =  T2.student_id GROUP BY T2.student_id HAVING count(*)  >=  2
SELECT T1.name FROM highschooler AS T1 JOIN likes AS T2 ON T1.id  =  T2.student_id GROUP BY T2.student_id HAVING count(*)  >=  2
SELECT T1.name FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.student_id WHERE T1.grade  >  5 GROUP BY T2.student_id HAVING count(*)  >=  2
SELECT T1.name FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.friend_id WHERE T1.grade  >  5 GROUP BY T2.student_id HAVING count(*)  >=  2
SELECT count(*) FROM Likes AS T1 JOIN highschooler AS T2 ON T1.student_id  =  T2.id WHERE T2.name  =  'Kyle'
SELECT count(*) FROM Likes AS T1 JOIN highschooler AS T2 ON T1.student_id  =  T2.id WHERE T2.name  =  'Kyle'
SELECT avg(T1.grade) FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.friend_id GROUP BY T2.student_id
SELECT avg(T1.grade) FROM highschooler AS T1 JOIN friend AS T2 ON T1.id  =  T2.friend_id
SELECT min(grade) FROM highschooler WHERE id NOT IN (SELECT student_id FROM friend)
SELECT min(grade) FROM highschooler WHERE id NOT IN (SELECT student_id FROM Friend)
SELECT state FROM owners INTERSECT SELECT state FROM professionals
SELECT state FROM owners INTERSECT SELECT state FROM professionals
SELECT avg(T1.age) FROM dogs AS T1 JOIN treatments AS T2 ON T1.dog_id  =  T2.dog_id
SELECT avg(T1.age) FROM dogs AS T1 JOIN treatments AS T2 ON T1.dog_id  =  T2.dog_id
SELECT T2.cell_phone ,  T2.last_name ,  T2.professional_id FROM Treatments AS T1 JOIN Professionals AS T2 ON T1.professional_id  =  T2.professional_id WHERE T2.state  =  "Indiana" GROUP BY T2.professional_id HAVING count(*)  >  2
SELECT T1.professional_id ,  T1.last_name ,  T1.cell_number FROM professionals AS T1 JOIN treatments AS T2 ON T1.professional_id  =  T2.professional_id WHERE T1.state  =  "Indiana" UNION SELECT T1.professional_id ,  T1.last_name ,  T1.cell_number FROM professionals AS T1 JOIN treatments AS T2 ON T1.professional_id  =  T2.professional_id GROUP BY T1.professional_id HAVING count(*)  >  2
SELECT T1.name FROM dogs AS T1 JOIN treatments AS T2 ON T1.dog_id  =  T2.dog_id GROUP BY T1.dog_id HAVING sum(T2.cost_of_treatment)  >  1000
SELECT T1.name FROM dogs AS T1 JOIN treatments AS T2 ON T1.dog_id  =  T2.dog_id JOIN owners AS T3 ON T1.owner_id  =  T3.owner_id GROUP BY T1.dog_id HAVING sum(T2.cost_of_treatment)  <=  1000
SELECT first_name FROM professionals UNION SELECT first_name FROM owners EXCEPT SELECT name FROM dogs
SELECT first_name FROM professionals UNION SELECT first_name FROM owners EXCEPT SELECT name FROM dogs
SELECT professional_id ,  role_code ,  email_address FROM professionals EXCEPT SELECT professional_id ,  role_code ,  email_address FROM treatments
SELECT professional_id ,  role_code ,  first_name ,  last_name ,  email_address FROM professionals EXCEPT SELECT T2.professional_id ,  T2.role_code ,  T1.first_name ,  T1.last_name ,  T1.email_address FROM treatments AS T1 JOIN professionals AS T2 ON T1.professional_id  =  T2.professional_id
SELECT T1.owner_id ,  T2.first_name ,  T2.last_name FROM dogs AS T1 JOIN owners AS T2 ON T1.owner_id  =  T2.owner_id GROUP BY T1.owner_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.owner_id ,  T2.first_name ,  T2.last_name FROM dogs AS T1 JOIN owners AS T2 ON T1.owner_id  =  T2.owner_id GROUP BY T1.owner_id ORDER BY count(*) DESC LIMIT 1
SELECT T2.professional_id ,  T1.role_code ,  T1.first_name FROM professionals AS T1 JOIN treatments AS T2 ON T1.professional_id  =  T2.professional_id GROUP BY T2.professional_id HAVING count(*)  >=  2
SELECT T2.professional_id ,  T1.role_code ,  T1.first_name FROM professionals AS T1 JOIN treatments AS T2 ON T1.professional_id  =  T2.professional_id GROUP BY T2.professional_id HAVING count(*)  >=  2
SELECT T1.breed_name FROM breeds AS T1 JOIN dogs AS T2 ON T1.breed_code  =  T2.breed_code GROUP BY T1.breed_name ORDER BY count(*) DESC LIMIT 1
SELECT T1.breed_name FROM breeds AS T1 JOIN dogs AS T2 ON T1.breed_code  =  T2.breed_code GROUP BY T1.breed_name ORDER BY count(*) DESC LIMIT 1
SELECT T1.owner_id ,  T2.last_name FROM Treatments AS T1 JOIN OWNERS AS T2 ON T1.dog_id  =  T2.owner_id GROUP BY T1.dog_id ORDER BY count(*) DESC LIMIT 1
SELECT T1.owner_id ,  T2.last_name FROM Dogs AS T1 JOIN OWNERS AS T2 ON T1.owner_id  =  T2.owner_id JOIN Treatments AS T3 ON T1.dog_id  =  T3.dog_id GROUP BY T1.owner_id ORDER BY sum(T3.cost_of_treatment) DESC LIMIT 1
SELECT T2.treatment_type_description FROM Treatments AS T1 JOIN Treatment_Types AS T2 ON T1.treatment_type_code  =  T2.treatment_type_code GROUP BY T1.treatment_type_code ORDER BY sum(T1.cost_of_treatment) ASC LIMIT 1
SELECT T2.treatment_type_description FROM Treatments AS T1 JOIN Treatment_Types AS T2 ON T1.treatment_type_code  =  T2.treatment_type_code GROUP BY T1.treatment_type_code ORDER BY sum(T1.cost_of_treatment) ASC LIMIT 1
SELECT T1.owner_id ,  T1.zip_code FROM owners AS T1 JOIN dogs AS T2 ON T1.owner_id  =  T2.owner_id JOIN treatments AS T3 ON T2.dog_id  =  T3.dog_id JOIN charges AS T4 ON T3.treatment_type_code  =  T4.charge_type ORDER BY sum(T4.charge_amount) DESC LIMIT 1
SELECT T1.owner_id ,  T1.zip_code FROM owners AS T1 JOIN dogs AS T2 ON T1.owner_id  =  T2.owner_id JOIN treatments AS T3 ON T2.dog_id  =  T3.dog_id JOIN charge AS T4 ON T4.charge_type  =  'Treatment' GROUP BY T1.owner_id ORDER BY sum(T4.charge_amount) DESC LIMIT 1
SELECT T2.cell_phone ,  T1.professional_id FROM treatments AS T1 JOIN professionals AS T2 ON T1.professional_id  =  T2.professional_id GROUP BY T1.professional_id HAVING count(*)  >=  2
SELECT T2.cell_number ,  T1.professional_id FROM Treatments AS T1 JOIN Professionals AS T2 ON T1.professional_id  =  T2.professional_id GROUP BY T1.professional_id HAVING count(*)  >=  2
SELECT T2.first_name ,  T2.last_name FROM Treatments AS T1 JOIN Professionals AS T2 ON T1.professional_id  =  T2.professional_id WHERE T1.cost_of_treatment  <  (SELECT avg(cost_of_treatment) FROM Treatments)
SELECT T1.first_name ,  T1.last_name FROM professionals AS T1 JOIN treatments AS T2 ON T1.professional_id  =  T2.professional_id WHERE T2.cost_of_treatment  <  ( SELECT avg(cost_of_treatment) FROM treatments )
SELECT T1.date_of_treatment ,  T2.first_name FROM Treatments AS T1 JOIN Professionals AS T2 ON T1.professional_id  =  T2.professional_id
SELECT T1.date_of_treatment ,  T2.first_name FROM Treatments AS T1 JOIN Professionals AS T2 ON T1.professional_id  =  T2.professional_id
SELECT T2.cost_of_treatment ,  T3.treatment_type_description FROM Treatments AS T2 JOIN Treatment_Types AS T3 ON T2.treatment_type_code  =  T3.treatment_type_code
SELECT T1.cost_of_treatment ,  T2.treatment_type_description FROM Treatments AS T1 JOIN Treatment_Types AS T2 ON T1.treatment_type_code  =  T2.treatment_type_code
SELECT T1.first_name ,  T1.last_name ,  T2.size_description FROM owners AS T1 JOIN dogs AS T2 ON T1.dog_id  =  T2.dog_id
SELECT T1.first_name ,  T1.last_name ,  T2.size_description FROM owners AS T1 JOIN dogs AS T2 ON T1.dog_id  =  T2.dog_id
SELECT T1.first_name ,  T2.name FROM owners AS T1 JOIN dogs AS T2 ON T1.owner_id  =  T2.owner_id
SELECT T1.first_name ,  T2.name FROM OWNERS AS T1 JOIN dogs AS T2 ON T1.owner_id  =  T2.owner_id
SELECT T2.name ,  T1.date_of_treatment FROM Treatments AS T1 JOIN Dogs AS T2 ON T1.dog_id  =  T2.dog_id WHERE T2.breed_code  =  ( SELECT breed_code FROM Dogs GROUP BY breed_code ORDER BY count(*) DESC LIMIT 1 )
SELECT T1.name ,  T2.date_of_treatment FROM dogs AS T1 JOIN treatments AS T2 ON T1.dog_id  =  T2.dog_id GROUP BY T1.breed_code ORDER BY count(*) DESC LIMIT 1
SELECT T2.first_name ,  T1.name FROM dogs AS T1 JOIN owners AS T2 ON T1.owner_id  =  T2.owner_id WHERE T2.state  =  'VA'
SELECT T2.first_name ,  T3.name FROM owners AS T1 JOIN dogs AS T3 ON T1.owner_id = T3.owner_id JOIN states AS T2 ON T2.state = T1.state WHERE T2.state = "VA"
SELECT T1.date_arrived ,  T1.date_departed FROM dogs AS T1 JOIN treatments AS T2 ON T1.dog_id  =  T2.dog_id
SELECT T1.date_arrived ,  T1.date_departed FROM Dogs AS T1 JOIN Treatments AS T2 ON T1.dog_id  =  T2.dog_id
SELECT T1.last_name FROM owners AS T1 JOIN dogs AS T2 ON T1.owner_id  =  T2.owner_id ORDER BY T2.age LIMIT 1
SELECT T1.last_name FROM owners AS T1 JOIN dogs AS T2 ON T1.owner_id  =  T2.owner_id ORDER BY T2.age ASC LIMIT 1
SELECT email_address FROM professionals WHERE state  =  "Hawaii" OR state  =  "Wisconsin"
SELECT email_address FROM professionals WHERE state  =  "Hawaii" OR state  =  "Wisconsin"
SELECT date_arrived ,  date_departed FROM dogs
SELECT date_arrived ,  date_departed FROM dogs
SELECT count(DISTINCT dog_id) FROM treatments
SELECT count(DISTINCT dog_id) FROM treatments
SELECT count(DISTINCT professional_id) FROM treatments
SELECT count(DISTINCT professional_id) FROM treatments
SELECT role_code ,  street ,  city ,  state FROM professionals WHERE city LIKE '%West%'
SELECT role_code ,  street ,  city ,  state FROM professionals WHERE city LIKE '%West%'
SELECT first_name ,  last_name ,  email_address FROM OWNERS WHERE state LIKE '%North%'
SELECT first_name ,  last_name ,  email_address FROM OWNERS WHERE state LIKE '%North%'
SELECT count(*) FROM dogs WHERE age  <  (SELECT avg(age) FROM dogs)
SELECT count(*) FROM dogs WHERE age  <  (SELECT avg(age) FROM dogs)
SELECT cost_of_treatment FROM Treatments ORDER BY date_of_treatment DESC LIMIT 1
SELECT cost_of_treatment FROM Treatments ORDER BY date_of_treatment DESC LIMIT 1
SELECT count(*) FROM dogs WHERE dog_id NOT IN ( SELECT dog_id FROM treatments )
SELECT count(*) FROM dogs WHERE dog_id NOT IN ( SELECT dog_id FROM treatments )
SELECT count(*) FROM owners WHERE owner_id NOT IN (SELECT owner_id FROM dogs)
SELECT count(*) FROM owners WHERE owner_id NOT IN (SELECT owner_id FROM dogs)
SELECT count(*) FROM professionals WHERE professional_id NOT IN ( SELECT professional_id FROM treatments )
SELECT count(*) FROM professionals WHERE professional_id NOT IN ( SELECT professional_id FROM treatments )
SELECT name ,  age ,  weight FROM dogs WHERE abandoned_yn  =  '1'
SELECT name ,  age ,  weight FROM dogs WHERE abandoned_yn  =  '1'
SELECT avg(age) FROM dogs
SELECT avg(age) FROM dogs
SELECT max(age) FROM dogs
SELECT max(age) FROM dogs
SELECT charge_type ,  charge_amount FROM Charges
SELECT charge_type ,  charge_amount FROM Charges
SELECT charge_amount FROM charges ORDER BY charge_amount DESC LIMIT 1
SELECT charge_amount FROM charges ORDER BY charge_amount DESC LIMIT 1
SELECT email_address ,  cell_number ,  home_phone FROM professionals
SELECT email_address ,  cell_phone ,  home_phone FROM professionals
SELECT T1.breed_name ,  T2.size_description FROM breeds AS T1 JOIN sizes AS T2 ON T1.breed_code  =  T2.size_code
SELECT DISTINCT breed_code ,  size_code FROM dogs
SELECT T1.first_name ,  T3.treatment_type_description FROM professionals AS T1 JOIN treatments AS T2 ON T1.professional_id  =  T2.professional_id JOIN treatment_types AS T3 ON T2.treatment_type_code  =  T3.treatment_type_code
SELECT T1.first_name ,  T3.treatment_type_description FROM professionals AS T1 JOIN treatments AS T2 ON T1.professional_id  =  T2.professional_id JOIN treatment_types AS T3 ON T2.treatment_type_code  =  T3.treatment_type_code
SELECT count(*) FROM singer
SELECT count(*) FROM singer
SELECT Name FROM singer ORDER BY Net_Worth_Millions ASC
SELECT Name FROM singer ORDER BY Net_Worth_Millions ASC
SELECT Birth_Year ,  Citizenship FROM singer
SELECT Birth_Year ,  Citizenship FROM singer
SELECT Name FROM singer WHERE Citizenship != "France"
SELECT Name FROM singer WHERE Citizenship != "French"
SELECT Name FROM singer WHERE Birth_Year  =  1948 OR Birth_Year  =  1949
SELECT Name FROM singer WHERE Birth_Year  =  1948 OR Birth_Year  =  1949
SELECT Name FROM singer ORDER BY Net_Worth_Millions DESC LIMIT 1
SELECT Name FROM singer ORDER BY Net_Worth_Millions DESC LIMIT 1
SELECT Citizenship ,  COUNT(*) FROM singer GROUP BY Citizenship
SELECT Citizenship ,  COUNT(*) FROM singer GROUP BY Citizenship
SELECT Citizenship FROM singer GROUP BY Citizenship ORDER BY COUNT(*) DESC LIMIT 1
SELECT Citizenship FROM singer GROUP BY Citizenship ORDER BY COUNT(*) DESC LIMIT 1
SELECT Citizenship ,  max(Net_Worth_Millions) FROM singer GROUP BY Citizenship
SELECT Citizenship ,  max(Net_Worth_Millions) FROM singer GROUP BY Citizenship
SELECT T1.Title ,  T2.Name FROM song AS T1 JOIN singer AS T2 ON T1.Singer_ID  =  T2.Singer_ID
SELECT T1.Title ,  T2.Name FROM song AS T1 JOIN singer AS T2 ON T1.Singer_ID  =  T2.Singer_ID
SELECT DISTINCT T1.Name FROM singer AS T1 JOIN song AS T2 ON T1.Singer_ID  =  T2.Singer_ID WHERE T2.Sales  >  300000
SELECT DISTINCT T1.Name FROM singer AS T1 JOIN song AS T2 ON T1.Singer_ID  =  T2.Singer_ID WHERE T2.Sales  >  300000
SELECT T2.Name FROM song AS T1 JOIN singer AS T2 ON T1.Singer_ID  =  T2.Singer_ID GROUP BY T1.Singer_ID HAVING COUNT(*)  >  1
SELECT T2.Name FROM singer AS T1 JOIN song AS T2 ON T1.Singer_ID  =  T2.Singer_ID GROUP BY T1.Singer_ID HAVING COUNT(*)  >  1
SELECT T1.Name ,  sum(T2.Sales) FROM singer AS T1 JOIN song AS T2 ON T1.Singer_ID  =  T2.Singer_ID GROUP BY T1.Singer_ID
SELECT T1.Name ,  sum(T2.Sales) FROM singer AS T1 JOIN song AS T2 ON T1.Singer_ID  =  T2.Singer_ID GROUP BY T1.Name
SELECT Name FROM singer WHERE Singer_ID NOT IN (SELECT Singer_ID FROM song)
SELECT Singer_ID ,  Name FROM singer WHERE Singer_ID NOT IN (SELECT Singer_ID FROM song)
SELECT Citizenship FROM singer WHERE Birth_Year  <  1945 INTERSECT SELECT Citizenship FROM singer WHERE Birth_Year  >  1955
SELECT Citizenship FROM singer WHERE Birth_Year  <  1945 INTERSECT SELECT Citizenship FROM singer WHERE Birth_Year  >  1955
SELECT count(*) FROM Other_Available_features
SELECT T1.feature_type_name FROM Ref_Feature_Types AS T1 JOIN Other_Available_Features AS T2 ON T1.feature_type_code  =  T2.feature_type_code WHERE T2.feature_name  =  "AirCon"
SELECT T1.property_type_description FROM Ref_Property_Types AS T1 JOIN Properties AS T2 ON T1.property_type_code  =  T2.property_type_code
SELECT property_name FROM properties WHERE property_type_code  =  'hse' OR property_type_code  =  'apt' AND room_count  >  1
