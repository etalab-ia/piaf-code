/*
 * Computing Wikipedia's internal PageRanks

 * Copyright (c) 2020 Project Nayuki. (MIT License)
 * https://www.nayuki.io/page/computing-wikipedias-internal-pageranks
 *
 * Adapted by Etalab in the context of the PIAF project
 * https://piaf.etalab.studio
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and associated documentation files (the "Software"), to deal in
 * the Software without restriction, including without limitation the rights to
 * use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 * the Software, and to permit persons to whom the Software is furnished to do so,
 * subject to the following conditions:
 * - The above copyright notice and this permission notice shall be included in
 *   all copies or substantial portions of the Software.
 * - The Software is provided "as is", without warranty of any kind, express or
 *   implied, including but not limited to the warranties of merchantability,
 *   fitness for a particular purpose and noninfringement. In no event shall the
 *   authors or copyright holders be liable for any claim, damages or other
 *   liability, whether in an action of contract, tort or otherwise, arising from,
 *   out of or in connection with the Software or the use or other dealings in the
 *   Software.
 *
 */

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;


/* 
 * Reads a text file with one page title per line, sorts the titles by descending PageRank, and writes
 * to a new text file. Requires raw data files already computed by the program "wikipediapagerank".
 */
public final class SortPageTitlesByPagerank {
	
	/*---- Input/output files configuration ----*/
	
	// User input/output files
	private static final File PAGE_TITLES_INPUT_FILE = new File("page-titles.txt");
	private static final File PAGE_TITLES_OUTPUT_FILE = new File("page-titles-sorted.txt");
	
	// Precomputed data files
	private static final File PAGE_ID_TITLE_RAW_FILE = new File("wikipedia-pagerank-page-id-title.raw");  // For caching
	private static final File PAGERANK_RAW_FILE = new File("wikipedia-pageranks.raw");
	
	
	/*---- Main program ----*/
	
	public static void main(String[] args) throws IOException {
		// Read title-ID map
		Map<String,Integer> titleToId = PageIdTitleMap.readRawFile(PAGE_ID_TITLE_RAW_FILE);
		
		// Read page titles to sort
		Set<String> titles = new HashSet<>();
		BufferedReader in0 = new BufferedReader(new InputStreamReader(new FileInputStream(PAGE_TITLES_INPUT_FILE), "UTF-8"));
		try {
			while (true) {
				String line = in0.readLine();
				if (line == null)
					break;
				if (titles.contains(line))
					System.out.println("Duplicate removed: " + line);
				else if (!titleToId.containsKey(line))
					System.out.println("Nonexistent page title removed: " + line);
				else
					titles.add(line);
			}
		} finally {
			in0.close();
		}
		
		// Read all PageRanks
		double[] pageranks = new double[(int)(PAGERANK_RAW_FILE.length() / 8)];
		DataInputStream in1 = new DataInputStream(new BufferedInputStream(new FileInputStream(PAGERANK_RAW_FILE)));
		try {
			for (int i = 0; i < pageranks.length; i++)
				pageranks[i] = in1.readDouble();
		} finally {
			in1.close();
		}
		
		// Sort and write output
		List<Entry> entries = new ArrayList<>();
		for (String title : titles)
			entries.add(new Entry(pageranks[titleToId.get(title)], title));
		Collections.sort(entries);
		PrintWriter out = new PrintWriter(new OutputStreamWriter(new FileOutputStream(PAGE_TITLES_OUTPUT_FILE), "UTF-8"));
		try {
			for (Entry e : entries)
				out.printf("%.3f\t%s\n", Math.log10(e.pagerank), e.title);
		} finally {
			out.close();
		}
	}
	
	
	
	/*---- Helper data structure ----*/
	
	private static final class Entry implements Comparable<Entry> {
		
		public final double pagerank;
		public final String title;
		
		
		public Entry(double pr, String tit) {
			pagerank = pr;
			title = tit;
		}
		
		
		public int compareTo(Entry other) {
			int temp = Double.compare(other.pagerank, pagerank);
			if (temp != 0)
				return temp;  // Primary: Sort descending by PageRank
			else
				return title.compareTo(other.title);  // Secondary: Sort ascending by title
		}
		
	}
	
	
	
	private SortPageTitlesByPagerank() {}  // Not instantiable
	
}
